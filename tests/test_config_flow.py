"""Tests for cloudflare_tunnel_monitor.config_flow.validate_input.

These exercise the branching logic that decides whether a config flow
submission (initial setup or reconfigure) is accepted: at least one of
API credentials or a metrics URL must be present, account_id/api_key
must be provided together (not partially), and each configured method
is actually validated against a (mocked) HTTP response.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.cloudflare_tunnel_monitor import config_flow as cf


def _make_response(status: int, text_body: str = ""):
    """Build a mock aiohttp response usable as an async context manager."""
    resp = AsyncMock()
    resp.status = status
    resp.text = AsyncMock(return_value=text_body)
    resp.__aenter__ = AsyncMock(return_value=resp)
    resp.__aexit__ = AsyncMock(return_value=False)
    return resp


def _make_session(get_response):
    session = MagicMock()
    session.get = MagicMock(return_value=get_response)
    return session


@pytest.fixture
def hass():
    """A placeholder hass object; async_get_clientsession is mocked in tests
    that need it, so this never needs to be a real HomeAssistant instance."""
    return object()


async def test_empty_input_requires_a_method(hass):
    errors = await cf.validate_input(hass, {})
    assert errors == {"base": "no_method_configured"}


async def test_account_id_without_api_key_is_incomplete(hass):
    errors = await cf.validate_input(hass, {"account_id": "abc"})
    assert errors == {"base": "incomplete_api_credentials"}


async def test_api_key_without_account_id_is_incomplete(hass):
    errors = await cf.validate_input(hass, {"api_key": "abc"})
    assert errors == {"base": "incomplete_api_credentials"}


async def test_metrics_url_only_valid_response_has_no_errors(hass):
    with patch.object(cf, "async_get_clientsession") as get_session:
        get_session.return_value = _make_session(
            _make_response(200, "# HELP foo bar\nfoo 1\n")
        )
        errors = await cf.validate_input(
            hass, {"metrics_url": "http://10.0.0.5:20241/metrics"}
        )
    assert errors == {}


async def test_metrics_url_only_unreachable_is_cannot_connect_metrics(hass):
    with patch.object(cf, "async_get_clientsession") as get_session:
        get_session.return_value = _make_session(_make_response(500))
        errors = await cf.validate_input(
            hass, {"metrics_url": "http://10.0.0.5:20241/metrics"}
        )
    assert errors == {"base": "cannot_connect_metrics"}


async def test_both_methods_valid_has_no_errors(hass):
    with patch.object(cf, "async_get_clientsession") as get_session:
        get_session.return_value = _make_session(_make_response(200, "# HELP x\nx 1\n"))
        errors = await cf.validate_input(
            hass,
            {
                "account_id": "acct",
                "api_key": "key",
                "metrics_url": "http://10.0.0.5:20241/metrics",
            },
        )
    assert errors == {}


async def test_invalid_api_auth_is_invalid_auth(hass):
    with patch.object(cf, "async_get_clientsession") as get_session:
        get_session.return_value = _make_session(_make_response(401))
        errors = await cf.validate_input(hass, {"account_id": "acct", "api_key": "bad"})
    assert errors == {"base": "invalid_auth"}


async def test_api_credentials_unreachable_is_cannot_connect(hass):
    with patch.object(cf, "async_get_clientsession") as get_session:
        get_session.return_value = _make_session(_make_response(500))
        errors = await cf.validate_input(hass, {"account_id": "acct", "api_key": "key"})
    assert errors == {"base": "cannot_connect"}


def test_compute_unique_id_prefers_account_id():
    unique_id = cf._compute_unique_id(
        {"account_id": "acct", "api_key": "key", "metrics_url": "http://10.0.0.5/metrics"}
    )
    assert unique_id == "acct"


def test_compute_unique_id_falls_back_to_metrics_url():
    unique_id = cf._compute_unique_id({"metrics_url": "http://10.0.0.5/metrics"})
    assert unique_id == "http://10.0.0.5/metrics"


def test_compute_unique_id_none_when_neither_present():
    assert cf._compute_unique_id({}) is None
