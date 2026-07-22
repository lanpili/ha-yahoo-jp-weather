"""Yahoo! Japan weather data coordinator."""

from __future__ import annotations

import logging
from datetime import datetime

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import DEFAULT_UPDATE_INTERVAL, DOMAIN, USER_AGENT
from .parser import WeatherData, parse_weather_html
from .regions import validate_municipality_url

LOGGER = logging.getLogger(__name__)


class YahooJapanWeatherCoordinator(DataUpdateCoordinator[WeatherData]):
    """Fetch and parse Yahoo! Japan weather."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=DEFAULT_UPDATE_INTERVAL,
        )
        self.url = validate_municipality_url(entry.data[CONF_URL])
        self.last_error_category: str | None = None
        self.last_successful_update: datetime | None = None

    async def _async_update_data(self) -> WeatherData:
        session = async_get_clientsession(self.hass)
        try:
            async with session.get(
                self.url,
                headers={"User-Agent": USER_AGENT},
                timeout=aiohttp.ClientTimeout(total=20),
                allow_redirects=False,
            ) as response:
                if 300 <= response.status < 400:
                    self.last_error_category = "redirect"
                    raise UpdateFailed("Yahoo weather redirect was rejected")
                if response.status != 200:
                    self.last_error_category = f"http_{response.status}"
                    raise UpdateFailed(f"Yahoo returned HTTP {response.status}")
                html = await response.text(encoding="utf-8")
            data = parse_weather_html(html)
        except TimeoutError as err:
            self.last_error_category = "timeout"
            raise UpdateFailed(f"Unable to update Yahoo weather: {err}") from err
        except aiohttp.ClientError as err:
            self.last_error_category = "network"
            raise UpdateFailed(f"Unable to update Yahoo weather: {err}") from err
        except ValueError as err:
            self.last_error_category = "parse"
            raise UpdateFailed(f"Unable to update Yahoo weather: {err}") from err
        self.last_error_category = None
        self.last_successful_update = dt_util.now()
        return data
