"""Tests for cloudflare_tunnel_monitor's setup entry and Prometheus parsing."""

from unittest.mock import AsyncMock, MagicMock, patch

import custom_components.cloudflare_tunnel_monitor as cf_init
from custom_components.cloudflare_tunnel_monitor.const import CONF_METRICS_URL, DOMAIN


def test_parse_prometheus_text_unlabeled_and_labeled():
    text = (
        "# HELP cloudflared_tunnel_total_requests total\n"
        "# TYPE cloudflared_tunnel_total_requests counter\n"
        "cloudflared_tunnel_total_requests 42\n"
        'cloudflared_tunnel_server_locations{connection_id="0",edge_location="sjc08"} 1\n'
    )

    parsed = cf_init.parse_prometheus_text(text)

    assert parsed["unlabeled"]["cloudflared_tunnel_total_requests"] == 42.0
    assert parsed["labeled"]["cloudflared_tunnel_server_locations"] == [
        {"labels": {"connection_id": "0", "edge_location": "sjc08"}, "value": 1.0}
    ]


def test_parse_prometheus_text_ignores_malformed_lines():
    text = "not a metric line\ncloudflared_tunnel_total_requests 5\n"

    parsed = cf_init.parse_prometheus_text(text)

    assert parsed["unlabeled"] == {"cloudflared_tunnel_total_requests": 5.0}


async def test_setup_entry_local_only_skips_api_coordinator():
    """metrics_url with no account_id/api_key must not construct the API
    coordinator at all (it would otherwise crash on entry.data[CONF_API_KEY])."""
    hass = MagicMock()
    hass.data = {}
    hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)

    entry = MagicMock()
    entry.entry_id = "entry1"
    entry.data = {CONF_METRICS_URL: "http://10.0.0.5:20241/metrics"}

    with patch.object(cf_init, "CloudflaredMetricsCoordinator") as mock_metrics_coord:
        mock_metrics_coord.return_value.async_refresh = AsyncMock(return_value=None)
        result = await cf_init.async_setup_entry(hass, entry)

    assert result is True
    stored = hass.data[DOMAIN][entry.entry_id]
    assert stored["api_coordinator"] is None
    assert stored["metrics_coordinator"] is not None


async def test_setup_entry_with_credentials_builds_api_coordinator():
    hass = MagicMock()
    hass.data = {}
    hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)

    entry = MagicMock()
    entry.entry_id = "entry1"
    entry.data = {"account_id": "acct", "api_key": "key"}

    with patch.object(cf_init, "CloudflareApiCoordinator") as mock_api_coord:
        mock_api_coord.return_value.async_config_entry_first_refresh = AsyncMock(
            return_value=None
        )
        result = await cf_init.async_setup_entry(hass, entry)

    assert result is True
    stored = hass.data[DOMAIN][entry.entry_id]
    assert stored["api_coordinator"] is not None
    assert stored["metrics_coordinator"] is None
