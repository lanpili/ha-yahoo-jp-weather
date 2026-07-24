# Yahoo! Japan Weather for Home Assistant

[English](README.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md)

An unofficial Home Assistant custom integration that reads municipal forecasts from [Yahoo!天気・災害](https://weather.yahoo.co.jp/weather/) and Yahoo's one-hour App forecast feed.

> This project is not affiliated with or endorsed by Yahoo Japan Corporation. Yahoo does not provide an official public API for this use case. The integration uses public location pages and an endpoint used by the Yahoo weather app, so upstream changes may require an integration update.

## Features

- Guided location setup: **prefecture → forecast area → municipality**
- Reconfigure the location later without changing the existing weather entity ID
- No API key required
- Current condition based on the nearest Yahoo one-hour forecast slot
- True one-hour forecasts with temperature, precipitation probability, humidity, precipitation, wind direction, and wind speed
- Up to ten-day daily forecast with high/low temperature and precipitation probability
- Optional adaptive dashboard enhancement with Yahoo-style hourly details
- Home Assistant standard weather conditions
- English, Japanese, and Simplified Chinese UI translations
- 30-minute polling interval
- Existing legacy URL-based YAML imports remain compatible
- Invalid or stale Yahoo pages are rejected instead of replacing the last valid forecast
- Privacy-safe Home Assistant diagnostics

## Installation

### HACS custom repository

1. Open HACS in Home Assistant.
2. Open **Custom repositories**.
3. Add:
   ```text
   https://github.com/lanpili/ha-yahoo-jp-weather
   ```
4. Select category **Integration**.
5. Install **Yahoo! Japan Weather** and restart Home Assistant.

### Manual installation

Copy this directory:

```text
custom_components/yahoo_jp_weather
```

into:

```text
/config/custom_components/yahoo_jp_weather
```

Then restart Home Assistant.

### Optional adaptive dashboard enhancement

The integration works with Home Assistant's standard weather cards without this optional file. To add height-aware hourly details to a standard `weather-forecast` card:

1. Copy [`dashboard/yahoo-weather-card.js`](dashboard/yahoo-weather-card.js) to:
   ```text
   /config/www/yahoo-weather-card.js
   ```
2. Add a JavaScript module resource in **Settings → Dashboards → Resources**:
   ```text
   /local/yahoo-weather-card.js?v=2.2.0
   ```
3. Reload the frontend or fully restart the Home Assistant app.

Continue using the standard weather forecast card. The resource recognizes Yahoo weather entities by their attribution and adapts hourly content to the section-grid height:

- 3 rows: time, icon, and temperature
- 4 rows: adds precipitation probability
- 5 rows: adds precipitation amount and humidity
- 6 or more rows: adds Yahoo-style wind direction, arrow, and speed

At least six hourly columns remain visible on a 390 px-wide mobile layout. Chinese, Japanese, and English use the same layout and automatically follow Home Assistant's active interface language. Tapping any non-dragged part of the card opens weather details; horizontal forecast dragging remains available. This optional enhancement relies on Home Assistant frontend internals and may require an update after a frontend redesign. HACS installs the integration only; it does not install this optional dashboard resource.

## Configuration

1. Go to **Settings → Devices & services**.
2. Select **Add integration**.
3. Search for **Yahoo! Japan Weather**.
4. Select a prefecture, forecast area, and municipality.

The integration creates one `weather.*` entity for each municipality. Additional locations can be added by running the configuration flow again.

To change an existing location, open the integration's config-entry menu and select **Reconfigure**. The current selections are prefilled, and the existing entity ID is preserved.

## Forecast data

| Data | Availability |
|---|---|
| Condition and temperature | Current nearest one-hour forecast |
| Hourly forecast | Yahoo App one-hour forecast |
| Daily forecast | Yahoo App daily forecast (up to 10 days) |
| Humidity | One-hour forecast |
| Precipitation | One-hour amount and probability; daily probability where published |
| Wind | Direction and speed from the one-hour forecast |

The “current” temperature is forecast data, not a local weather-station observation.

## Limitations

- Yahoo! JAPAN does not provide an official public API for this use case. The bundled App client identifier is not a user API key.
- The integration depends on Yahoo's current location-page structure and App forecast response format.
- Do not reduce the 30-minute polling interval.
- Weather descriptions and municipality names are provided by Yahoo in Japanese; standard HA weather states are localized by Home Assistant.

## Reliability, security, and privacy

- A new or reconfigured municipality is fetched and parsed **before** the config entry is saved. If validation fails, the existing location remains unchanged.
- Legacy URLs, discovered links, and final location pages are restricted to HTTPS municipality pages on `weather.yahoo.co.jp`. Cross-site redirects are rejected.
- The parsers reject missing or stale publication timestamps, expired forecasts, unusable responses, and implausible numeric values.
- Yahoo can observe your public IP address, selected municipality code, request time, and the integration User-Agent when Home Assistant polls every 30 minutes.
- Downloaded HTML and forecast responses are not stored. Home Assistant diagnostics omit the municipality name, source URL, and forecast contents.

## Troubleshooting

1. Update to the latest integration release and restart Home Assistant.
2. Open **Settings → Devices & services → Yahoo! Japan Weather** and check whether the config entry reports a retry or setup error.
3. Download diagnostics from the config entry. They contain update status and forecast counts but intentionally exclude the selected location.
4. Check Home Assistant logs for `yahoo_jp_weather`. A parser error may indicate that Yahoo changed its page structure; please submit a redacted bug report.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md). The full local quality gate is:

```bash
python -m pip install --requirement requirements-test.txt
pytest -q --cov=custom_components.yahoo_jp_weather --cov-report=term-missing
ruff check custom_components tests scripts
ruff format --check custom_components tests scripts
mypy custom_components/yahoo_jp_weather
```

## License

MIT License. See [LICENSE](LICENSE).
