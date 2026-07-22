"""Config flow for Yahoo! Japan Weather."""

from __future__ import annotations

import re
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_URL
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import CONF_ENTITY_UNIQUE_ID, CONF_NAME, DOMAIN
from .regions import (
    BASE_URL,
    PREFECTURES,
    LocationOption,
    parse_forecast_areas,
    parse_location_url,
    parse_municipalities,
)

CONF_PREFECTURE = "prefecture"
CONF_FORECAST_AREA = "forecast_area"
CONF_MUNICIPALITY = "municipality"


def _unique_id(url: str) -> str:
    match = re.search(r"/(\d+)\.html(?:\?.*)?$", url)
    return match.group(1) if match else url


def _selector(options: list[LocationOption] | dict[str, str]) -> SelectSelector:
    if isinstance(options, dict):
        choices = [
            SelectOptionDict(value=value, label=label)
            for value, label in options.items()
        ]
    else:
        choices = [
            SelectOptionDict(value=option.code, label=option.name) for option in options
        ]
    return SelectSelector(
        SelectSelectorConfig(options=choices, mode=SelectSelectorMode.DROPDOWN)
    )


class YahooJapanWeatherConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle Yahoo! Japan Weather configuration."""

    VERSION = 1

    def __init__(self) -> None:
        self._prefecture_code: str | None = None
        self._forecast_areas: dict[str, LocationOption] = {}
        self._forecast_area: LocationOption | None = None
        self._municipalities: dict[str, LocationOption] = {}
        self._reconfigure_entry: config_entries.ConfigEntry | None = None
        self._default_prefecture = "13"
        self._default_forecast_area: str | None = None
        self._default_municipality: str | None = None

    async def _async_fetch_html(self, url: str) -> str:
        session = async_get_clientsession(self.hass)
        async with session.get(
            url,
            headers={"User-Agent": "HomeAssistant YahooJapanWeather/1.2"},
            timeout=aiohttp.ClientTimeout(total=20),
        ) as response:
            response.raise_for_status()
            return await response.text(encoding="utf-8")

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Select a prefecture."""
        return await self._async_step_prefecture("user", user_input)

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Change the location of an existing config entry."""
        if self._reconfigure_entry is None:
            self._reconfigure_entry = self._get_reconfigure_entry()
            current = parse_location_url(self._reconfigure_entry.data[CONF_URL])
            if current is not None:
                (
                    self._default_prefecture,
                    self._default_forecast_area,
                    self._default_municipality,
                ) = current
        return await self._async_step_prefecture("reconfigure", user_input)

    async def _async_step_prefecture(
        self, step_id: str, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Select a prefecture for setup or reconfiguration."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self._prefecture_code = user_input[CONF_PREFECTURE]
            self._forecast_areas = {}
            self._forecast_area = None
            self._municipalities = {}
            try:
                html = await self._async_fetch_html(
                    f"{BASE_URL}/weather/jp/{self._prefecture_code}/"
                )
                areas = parse_forecast_areas(html, self._prefecture_code)
            except (aiohttp.ClientError, TimeoutError):
                errors["base"] = "cannot_connect"
            else:
                if not areas:
                    errors["base"] = "no_locations"
                else:
                    self._forecast_areas = {item.code: item for item in areas}
                    if len(areas) == 1:
                        self._forecast_area = areas[0]
                        return await self.async_step_municipality()
                    return await self.async_step_forecast_area()

        return self.async_show_form(
            step_id=step_id,
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_PREFECTURE, default=self._default_prefecture
                    ): _selector(PREFECTURES)
                }
            ),
            errors=errors,
        )

    async def async_step_forecast_area(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Select a Yahoo forecast area."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self._forecast_area = self._forecast_areas[user_input[CONF_FORECAST_AREA]]
            self._municipalities = {}
            return await self.async_step_municipality()
        default = self._default_forecast_area
        field = (
            vol.Required(CONF_FORECAST_AREA, default=default)
            if default in self._forecast_areas
            else vol.Required(CONF_FORECAST_AREA)
        )
        return self.async_show_form(
            step_id="forecast_area",
            data_schema=vol.Schema(
                {field: _selector(list(self._forecast_areas.values()))}
            ),
            errors=errors,
        )

    async def async_step_municipality(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Fetch and select a municipality."""
        if self._prefecture_code is None or self._forecast_area is None:
            return await self.async_step_user()

        errors: dict[str, str] = {}
        if not self._municipalities:
            try:
                html = await self._async_fetch_html(self._forecast_area.url)
                municipalities = parse_municipalities(
                    html, self._prefecture_code, self._forecast_area.code
                )
            except (aiohttp.ClientError, TimeoutError):
                errors["base"] = "cannot_connect"
            else:
                if not municipalities:
                    errors["base"] = "no_locations"
                else:
                    self._municipalities = {item.code: item for item in municipalities}

        if user_input is not None and self._municipalities:
            location = self._municipalities[user_input[CONF_MUNICIPALITY]]
            if self._reconfigure_entry is not None:
                duplicate = next(
                    (
                        entry
                        for entry in self.hass.config_entries.async_entries(DOMAIN)
                        if entry.entry_id != self._reconfigure_entry.entry_id
                        and entry.unique_id == location.code
                    ),
                    None,
                )
                if duplicate is not None:
                    errors["base"] = "location_in_use"
                else:
                    stable_id = self._reconfigure_entry.data.get(
                        CONF_ENTITY_UNIQUE_ID,
                        self._reconfigure_entry.unique_id
                        or self._reconfigure_entry.entry_id,
                    )
                    return self.async_update_reload_and_abort(
                        self._reconfigure_entry,
                        unique_id=location.code,
                        title=location.name,
                        data={
                            **self._reconfigure_entry.data,
                            CONF_ENTITY_UNIQUE_ID: stable_id,
                            CONF_NAME: location.name,
                            CONF_URL: location.url,
                        },
                    )
            else:
                await self.async_set_unique_id(location.code)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=location.name,
                    data={
                        CONF_ENTITY_UNIQUE_ID: location.code,
                        CONF_NAME: location.name,
                        CONF_URL: location.url,
                    },
                )

        default = self._default_municipality
        field = (
            vol.Required(CONF_MUNICIPALITY, default=default)
            if default in self._municipalities
            else vol.Required(CONF_MUNICIPALITY)
        )
        return self.async_show_form(
            step_id="municipality",
            data_schema=vol.Schema(
                {field: _selector(list(self._municipalities.values()))}
            ),
            errors=errors,
        )

    async def async_step_import(self, user_input: dict[str, Any]) -> FlowResult:
        """Import legacy YAML configuration."""
        unique_id = _unique_id(user_input[CONF_URL])
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=user_input[CONF_NAME],
            data={**user_input, CONF_ENTITY_UNIQUE_ID: unique_id},
        )
