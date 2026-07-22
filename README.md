# Yahoo! Japan Weather for Home Assistant

[English](README.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md)

An unofficial Home Assistant custom integration that reads municipal forecasts from [Yahoo!天気・災害](https://weather.yahoo.co.jp/weather/).

> This project is not affiliated with or endorsed by Yahoo Japan Corporation. It parses public web pages rather than an official API, so upstream HTML changes may require an integration update.

## Features

- Guided location setup: **prefecture → forecast area → municipality**
- Reconfigure the location later without changing the existing weather entity ID
- No API key required
- Current condition based on the nearest Yahoo three-hour forecast slot
- Three-hour forecasts with temperature, humidity, precipitation, wind direction, and wind speed
- Eight-day daily forecast with high/low temperature and precipitation probability
- Home Assistant standard weather conditions
- English, Japanese, and Simplified Chinese UI translations
- 30-minute polling interval
- Existing legacy URL-based YAML imports remain compatible

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
| Condition and temperature | Current nearest 3-hour forecast |
| Hourly forecast | Yahoo 3-hour forecast, exposed as HA hourly forecast |
| Daily forecast | Today, tomorrow, and Yahoo weekly forecast (up to 8 days) |
| Humidity | 3-hour forecast |
| Precipitation | 3-hour amount; daily probability where published |
| Wind | Direction and speed from the 3-hour forecast |

The “current” temperature is forecast data, not a local weather-station observation.

## Limitations

- Yahoo! JAPAN does not provide an official public API for this use case.
- The integration depends on the current HTML structure of Yahoo!天気・災害.
- Do not reduce the 30-minute polling interval.
- Weather descriptions and municipality names are provided by Yahoo in Japanese; standard HA weather states are localized by Home Assistant.

## Development

Run the local tests with:

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q custom_components
```

## License

MIT License. See [LICENSE](LICENSE).
