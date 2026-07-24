"""Weather entity for Yahoo! Japan Weather."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.weather import (
    Forecast,
    SingleCoordinatorWeatherEntity,
    WeatherEntityFeature,
)
from homeassistant.const import (
    CONF_URL,
    UnitOfPrecipitationDepth,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from .adapter import daily_forecasts_for_ha, hourly_forecasts_for_ha
from .const import CONF_ENTITY_UNIQUE_ID, DOMAIN
from .coordinator import YahooJapanWeatherCoordinator

if TYPE_CHECKING:
    from . import YahooConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: YahooConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([YahooJapanWeatherEntity(entry.runtime_data, entry)])


class YahooJapanWeatherEntity(
    SingleCoordinatorWeatherEntity[YahooJapanWeatherCoordinator]
):
    """Yahoo! Japan weather entity."""

    _attr_has_entity_name = True
    _attr_translation_key = "forecast"
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_precipitation_unit = UnitOfPrecipitationDepth.MILLIMETERS
    _attr_native_wind_speed_unit = UnitOfSpeed.METERS_PER_SECOND
    _attr_supported_features = (
        WeatherEntityFeature.FORECAST_HOURLY | WeatherEntityFeature.FORECAST_DAILY
    )
    _attr_attribution = "Weather data provided by Yahoo! JAPAN"

    def __init__(
        self, coordinator: YahooJapanWeatherCoordinator, entry: YahooConfigEntry
    ) -> None:
        super().__init__(coordinator=coordinator)
        self._attr_unique_id = entry.data.get(
            CONF_ENTITY_UNIQUE_ID, entry.unique_id or entry.entry_id
        )
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, self._attr_unique_id)},
            manufacturer="Yahoo! JAPAN",
            name=entry.title,
            configuration_url=entry.data[CONF_URL],
        )

    @property
    def condition(self) -> str | None:
        return self.coordinator.data.current.condition

    @property
    def native_temperature(self) -> float | None:
        return self.coordinator.data.current.temperature

    @property
    def humidity(self) -> float | None:
        return self.coordinator.data.current.humidity

    @property
    def native_wind_speed(self) -> float | None:
        return self.coordinator.data.current.wind_speed

    @property
    def wind_bearing(self) -> float | None:
        return self.coordinator.data.current.wind_bearing

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "published_at": self.coordinator.data.published_at,
            "forecast_interval_hours": 1,
        }

    @callback
    def _async_forecast_hourly(self) -> list[Forecast] | None:
        return hourly_forecasts_for_ha(self.coordinator.data.hourly, now=dt_util.now())

    @callback
    def _async_forecast_daily(self) -> list[Forecast] | None:
        return daily_forecasts_for_ha(self.coordinator.data.daily, now=dt_util.now())
