import logging
from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_ACCOUNT_ID, CONF_API_KEY, CONF_METRICS_URL
from .coordinator import (
    CloudflareApiCoordinator,
    CloudflaredMetricsCoordinator,
    parse_prometheus_text,
)

__all__ = ["parse_prometheus_text"]

_LOGGER = logging.getLogger(__name__)


@dataclass
class CloudflareTunnelMonitorData:
    """Runtime data stored on the config entry."""

    api_coordinator: CloudflareApiCoordinator | None
    metrics_coordinator: CloudflaredMetricsCoordinator | None


type CloudflareTunnelMonitorConfigEntry = ConfigEntry[CloudflareTunnelMonitorData]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Cloudflare Tunnel component."""
    return True


async def async_setup_entry(
    hass: HomeAssistant, entry: CloudflareTunnelMonitorConfigEntry
) -> bool:
    """Set up Cloudflare Tunnel from a config entry."""
    api_coordinator: CloudflareApiCoordinator | None = None
    if entry.data.get(CONF_ACCOUNT_ID) and entry.data.get(CONF_API_KEY):
        api_coordinator = CloudflareApiCoordinator(hass, entry)
        await api_coordinator.async_config_entry_first_refresh()

    metrics_coordinator: CloudflaredMetricsCoordinator | None = None
    metrics_url = entry.data.get(CONF_METRICS_URL)
    if metrics_url:
        metrics_coordinator = CloudflaredMetricsCoordinator(hass, entry, metrics_url)
        try:
            await metrics_coordinator.async_refresh()
        except Exception as err:
            _LOGGER.warning(
                "Initial metrics refresh failed; continuing without metrics coordinator: %s",
                err,
            )
            metrics_coordinator = None

    entry.runtime_data = CloudflareTunnelMonitorData(
        api_coordinator=api_coordinator,
        metrics_coordinator=metrics_coordinator,
    )

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: CloudflareTunnelMonitorConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_forward_entry_unload(entry, "sensor")
