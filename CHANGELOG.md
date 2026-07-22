# Changelog

## 1.2.0

- Add Home Assistant's native reconfigure flow for changing the selected location.
- Preserve the existing weather entity ID and Lovelace references when the location changes.
- Preselect the current prefecture, forecast area, and municipality during reconfiguration.
- Prevent selecting a municipality that is already used by another config entry.

## 1.1.0

- Add guided location selection: prefecture, forecast area, and municipality.
- Add Yahoo weekly forecast parsing for up to eight daily forecasts.
- Add daily precipitation probability.
- Add English, Japanese, and Simplified Chinese configuration UI.
- Preserve compatibility with legacy URL-based YAML imports.

## 1.0.0

- Initial Home Assistant weather entity.
- Add three-hour forecasts, two-day daily forecast, wind, humidity, and precipitation.
