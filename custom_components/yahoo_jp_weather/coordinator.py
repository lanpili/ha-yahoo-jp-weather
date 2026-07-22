"""Yahoo! Japan weather data coordinator."""

from __future__ import annotations

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_UPDATE_INTERVAL, DOMAIN
from .parser import WeatherData, parse_weather_html


class YahooJapanWeatherCoordinator(DataUpdateCoordinator[WeatherData]):
    """Fetch and parse Yahoo! Japan weather."""

    def __init__(self, hass: HomeAssistant, url: str) -> None:
        super().__init__(
            hass,
            logger=__import__("logging").getLogger(__name__),
            name=DOMAIN,
            update_interval=DEFAULT_UPDATE_INTERVAL,
        )
        self.url = url

    async def _async_update_data(self) -> WeatherData:
        session = async_get_clientsession(self.hass)
        try:
            async with session.get(
                self.url,
                headers={"User-Agent": "HomeAssistant YahooJapanWeather/1.0"},
                timeout=aiohttp.ClientTimeout(total=20),
            ) as response:
                if response.status != 200:
                    raise UpdateFailed(f"Yahoo returned HTTP {response.status}")
                html = await response.text(encoding="utf-8")
            return parse_weather_html(html)
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            raise UpdateFailed(f"Unable to update Yahoo weather: {err}") from err
