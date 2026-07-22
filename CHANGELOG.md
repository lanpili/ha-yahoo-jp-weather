# Changelog

## 1.3.0

- Harden Yahoo HTML section tracking and ignore script, style, template, and noscript content.
- Reject missing or stale publication timestamps, expired forecasts, unusable tables, and implausible weather values.
- Restrict imported, discovered, and requested URLs to Yahoo HTTPS municipality pages and reject redirects.
- Validate a new municipality before atomically committing a reconfiguration.
- Adopt typed config-entry runtime data and explicitly associate the update coordinator with its config entry for Home Assistant 2026.8 compatibility.
- Add config-entry version 2 migration while preserving the existing weather entity unique ID.
- Add privacy-safe diagnostics and categorized update errors.
- Expand standard Home Assistant weather condition mapping and parser format compatibility.
- Add real Home Assistant lifecycle, config-flow, coordinator, weather forecast, diagnostics, lint, typing, and coverage checks.
- Add pinned CI actions, weekly low-frequency live parsing probe, automated release assets, Dependabot, and community security templates.

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
