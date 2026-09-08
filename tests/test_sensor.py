"""Tests for cloudflare_tunnel_monitor.sensor's async_setup_entry.

Covers the case that motivated the api_coordinator-is-optional change:
setup must not crash when there is no Cloudflare API coordinator (e.g.
a metrics_url-only entry), and must simply add no tunnel entities.
"""

from unittest.mock import MagicMock

import custom_components.cloudflare_tunnel_monitor.sensor as cf_sensor
from custom_components.cloudflare_tunnel_monitor import CloudflareTunnelMonitorData


async def test_setup_entry_with_no_coordinators_adds_no_entities():
    hass = MagicMock()
    entry = MagicMock()
    entry.entry_id = "entry1"
    entry.data = {}
    entry.runtime_data = CloudflareTunnelMonitorData(
        api_coordinator=None, metrics_coordinator=None
    )

    added = []

    def async_add_entities(entities, update_before_add=False):
        added.extend(entities)

    await cf_sensor.async_setup_entry(hass, entry, async_add_entities)

    assert added == []


async def test_setup_entry_with_api_coordinator_adds_tunnel_sensors():
    hass = MagicMock()
    entry = MagicMock()
    entry.entry_id = "entry1"
    entry.data = {"account_id": "acct"}

    api_coordinator = MagicMock()
    api_coordinator.data = [{"id": "tunnel-1", "name": "home", "status": "healthy"}]

    entry.runtime_data = CloudflareTunnelMonitorData(
        api_coordinator=api_coordinator, metrics_coordinator=None
    )

    added = []

    def async_add_entities(entities, update_before_add=False):
        added.extend(entities)

    await cf_sensor.async_setup_entry(hass, entry, async_add_entities)

    assert len(added) == 1
    assert added[0]._tunnel_id == "tunnel-1"
