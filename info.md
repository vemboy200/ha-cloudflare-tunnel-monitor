# Cloudflare Tunnel Monitor Home Assistant Integration

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
![Cloudflare Tunnel Monitor|128](https://raw.githubusercontent.com/vemboy200/ha-cloudflare-tunnel-monitor/master/images/logo.png)

## *** This is a personal fork ***

This fork of [deadbeef3137/ha-cloudflare-tunnel-monitor](https://github.com/deadbeef3137/ha-cloudflare-tunnel-monitor) adds:
- **Local-only setup**: `metrics_url` alone now works, no Cloudflare API token required
- **Reconfigure support**: change your settings later via Settings → Devices & Services → Configure, without deleting and re-adding the integration

## *** IMPORTANT ***

Prometheus metrics support has been implemented and is now available in the latest release (v.2.2.1).

This feature was contributed by @tannerln7 — huge thanks for the great work and for sharing it with the community!

Thanks again to everyone involved! 🙌

## Description

This custom integration for Home Assistant allows users to monitor the status of their Cloudflare Tunnels directly from their Home Assistant instance. The integration fetches the status of Cloudflare Tunnels and presents it as sensor entities in Home Assistant.

## Installation

### Via HACS (Home Assistant Community Store)

1. Navigate to the HACS page on your Home Assistant instance.
2. Go to the "Integrations" tab and click the "Explore & Add Repositories" button.
3. Search for "Cloudflare Tunnel Monitor" and select it.
4. Click on "Install this repository in HACS".
5. Restart your Home Assistant instance.

### Manual Installation

1. Clone this repository or download the zip file.
2. Copy the `cloudflare_tunnel_monitor` directory from the `custom_components` directory in this repository to the `custom_components` directory on your Home Assistant instance.
3. Restart your Home Assistant instance.

## Configuration

### Cloudflare Setup
<span><strong style="color:deepskyblue;">1. Copy your Account ID.</strong></span>

![Account ID](https://raw.githubusercontent.com/deadbeef3137/imagenes-readme/master/AccountID.png)

<span><strong style="color:deepskyblue;">2. Create an API Token.</strong></span>

![API Token](https://raw.githubusercontent.com/deadbeef3137/imagenes-readme/master/API-Token.png)


### Via UI

1. Navigate to "Configuration" -> "Integrations" -> "+".
2. Search for "Cloudflare Tunnel Monitor" and select it.
3. Fill in the required information and click "Submit".

### Configuration Variables

You need **either** Cloudflare API credentials **or** a metrics URL (or both).

- `api_key` / `account_id` *(optional together)*: Your Cloudflare API Token with `Account:Cloudflare Tunnel:Read` permissions, and your Cloudflare Account ID. Must be provided together, not one without the other.
- `metrics_url` *(optional)*: The URL of your local cloudflared Prometheus metrics endpoint (e.g. `http://10.0.30.5:20241/metrics`). When provided, the integration creates additional sensors for QUIC transport, throughput, latency, process health, and more. Works entirely on its own, no Cloudflare API token needed.


## Usage

Upon successful configuration, the integration will create sensor entities for each Cloudflare Tunnel reflecting current tunnel status (healthy / degraded / inactive / down).

If a `metrics_url` is configured, the integration also scrapes cloudflared's Prometheus `/metrics` endpoint and exposes ~50 additional sensors covering QUIC RTT statistics, throughput rates, transport shape, proxy/RPC latency baselines, Go GC pause metrics, and process health counters.

## Support

Please raise issues specific to this fork (local-only setup, reconfigure flow) on [this repository](https://github.com/vemboy200/ha-cloudflare-tunnel-monitor/issues) rather than upstream.

## License

This integration is released under the [MIT License](https://opensource.org/licenses/MIT).

## Disclaimer

This project is not affiliated with or endorsed by Cloudflare.

