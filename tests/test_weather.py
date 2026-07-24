from homeassistant.const import UnitOfSpeed

from custom_components.yahoo_jp_weather.weather import YahooJapanWeatherEntity


def test_weather_entity_uses_meters_per_second() -> None:
    entity = object.__new__(YahooJapanWeatherEntity)
    assert entity.native_wind_speed_unit == UnitOfSpeed.METERS_PER_SECOND
