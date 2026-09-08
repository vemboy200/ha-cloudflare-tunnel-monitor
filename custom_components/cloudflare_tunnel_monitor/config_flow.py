import aiohttp
import async_timeout
import re
import voluptuous as vol
from urllib.parse import urlparse
from homeassistant import config_entries, exceptions
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import DOMAIN, CONF_API_KEY, CONF_ACCOUNT_ID, CONF_METRICS_URL, LABEL_API_KEY, LABEL_ACCOUNT_ID, LABEL_METRICS_URL, PLACEHOLDER_API_KEY, PLACEHOLDER_ACCOUNT_ID, PLACEHOLDER_METRICS_URL

# Constants
URL = "https://api.cloudflare.com/client/v4/user/tokens/verify"
TIMEOUT = 10

# Custom exceptions
class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""

class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""

DATA_SCHEMA = vol.Schema({
    vol.Optional(CONF_ACCOUNT_ID, description={LABEL_ACCOUNT_ID}): str,
    vol.Optional(CONF_API_KEY, description={LABEL_API_KEY}): str,
    vol.Optional(CONF_METRICS_URL, description={LABEL_METRICS_URL}): str,
})

async def validate_credentials(hass, data):
    """Validate the provided credentials are correct."""
    api_key = data["api_key"]

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }

    try:
        session = async_get_clientsession(hass)
        async with async_timeout.timeout(TIMEOUT):
            async with session.get(URL, headers=headers) as response:
                if response.status == 200:
                    return True
                elif response.status == 401:
                    raise InvalidAuth
                else:
                    raise CannotConnect
    except aiohttp.ClientError:
        raise CannotConnect
    except TimeoutError:
        raise CannotConnect

async def validate_metrics_endpoint(hass, url: str) -> bool:
    """Validate the provided metrics endpoint URL is reachable and Prometheus-like."""
    parsed = urlparse(url)
    if parsed.scheme not in ('http', 'https'):
        raise CannotConnect

    try:
        session = async_get_clientsession(hass)
        async with async_timeout.timeout(TIMEOUT):
            async with session.get(url) as response:
                if response.status != 200:
                    raise CannotConnect

                text = await response.text()
                lines = text.splitlines()
                for line in lines:
                    stripped = line.strip()
                    if stripped.startswith('# HELP') or stripped.startswith('# TYPE'):
                        return True
                    if re.match(r'^[a-zA-Z_:][a-zA-Z0-9_:]*(\{.*\})?\s+[-+]?[0-9]', stripped):
                        return True

                raise CannotConnect
    except aiohttp.ClientError:
        raise CannotConnect
    except TimeoutError:
        raise CannotConnect

async def validate_input(hass: HomeAssistant, user_input: dict) -> dict[str, str]:
    """Validate input shared by the initial setup and reconfigure flows.

    Either both account_id and api_key must be provided (to use the
    Cloudflare API), or metrics_url must be provided (to use a local
    cloudflared metrics endpoint only), or both. Returns a dict of
    errors, empty if the input is valid.
    """
    errors: dict[str, str] = {}

    account_id = user_input.get(CONF_ACCOUNT_ID)
    api_key = user_input.get(CONF_API_KEY)
    metrics_url = user_input.get(CONF_METRICS_URL)

    has_api_credentials = bool(account_id and api_key)
    has_partial_api_credentials = bool(account_id) != bool(api_key)

    if has_partial_api_credentials:
        errors["base"] = "incomplete_api_credentials"
        return errors

    if not has_api_credentials and not metrics_url:
        errors["base"] = "no_method_configured"
        return errors

    if has_api_credentials:
        try:
            await validate_credentials(hass, user_input)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except Exception:
            errors["base"] = "unknown"

    if not errors and metrics_url:
        try:
            await validate_metrics_endpoint(hass, metrics_url)
        except CannotConnect:
            errors["base"] = "cannot_connect_metrics"

    return errors

class CloudflareConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Cloudflare config flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle a flow initiated by the user."""
        errors = {}

        if user_input is not None:
            errors = await validate_input(self.hass, user_input)
            if not errors:
                return self.async_create_entry(title="Cloudflare Tunnel Monitor", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                CONF_API_KEY: PLACEHOLDER_API_KEY,
                CONF_ACCOUNT_ID: PLACEHOLDER_ACCOUNT_ID,
                CONF_METRICS_URL: PLACEHOLDER_METRICS_URL,
            }
        )

    async def async_step_reconfigure(self, user_input=None):
        """Handle reconfiguration of an existing entry.

        Lets an existing entry's account_id/api_key/metrics_url be added
        or changed later, without deleting and recreating it.
        """
        errors = {}
        reconfigure_entry = self._get_reconfigure_entry()

        if user_input is not None:
            errors = await validate_input(self.hass, user_input)
            if not errors:
                return self.async_update_reload_and_abort(
                    reconfigure_entry,
                    data=user_input,
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                DATA_SCHEMA, reconfigure_entry.data
            ),
            errors=errors,
            description_placeholders={
                CONF_API_KEY: PLACEHOLDER_API_KEY,
                CONF_ACCOUNT_ID: PLACEHOLDER_ACCOUNT_ID,
                CONF_METRICS_URL: PLACEHOLDER_METRICS_URL,
            }
        )
