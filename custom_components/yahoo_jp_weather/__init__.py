"""Yahoo! Japan Weather custom integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import CONF_URL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_ENTITY_UNIQUE_ID,
    CONF_NAME,
    CONFIG_VERSION,
    DEFAULT_NAME,
    DEFAULT_URL,
    DOMAIN,
)
from .coordinator import YahooJapanWeatherCoordinator
from .regions import parse_location_url, validate_municipality_url

type YahooConfigEntry = ConfigEntry[YahooJapanWeatherCoordinator]
LOGGER = logging.getLogger(__name__)


def _validate_yaml_url(value: Any) -> str:
    try:
        return validate_municipality_url(cv.url(value))
    except ValueError as err:
        raise vol.Invalid(str(err)) from err


CONFIG_SCHEMA = vol.Schema(
    {
        vol.Optional(DOMAIN): vol.Schema(
            {
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
                vol.Optional(CONF_URL, default=DEFAULT_URL): _validate_yaml_url,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Import the optional YAML bootstrap into a config entry."""
    if DOMAIN in config:
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": SOURCE_IMPORT},
                data=dict(config[DOMAIN]),
            )
        )
    return True


async def async_migrate_entry(hass: HomeAssistant, entry: YahooConfigEntry) -> bool:
    """Migrate legacy entries to canonical, stable version 2 data."""
    if entry.version > CONFIG_VERSION:
        return False
    if entry.version == CONFIG_VERSION:
        return True

    try:
        url = validate_municipality_url(entry.data[CONF_URL])
    except (KeyError, ValueError) as err:
        LOGGER.error("Cannot migrate invalid Yahoo weather URL: %s", err)
        return False

    location = parse_location_url(url)
    assert location is not None
    data = dict(entry.data)
    data[CONF_URL] = url
    data[CONF_ENTITY_UNIQUE_ID] = data.get(CONF_ENTITY_UNIQUE_ID) or (
        entry.unique_id or location[2]
    )
    hass.config_entries.async_update_entry(
        entry,
        data=data,
        unique_id=entry.unique_id or location[2],
        version=CONFIG_VERSION,
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: YahooConfigEntry) -> bool:
    """Set up Yahoo! Japan Weather from a config entry."""
    coordinator = YahooJapanWeatherCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    try:
        await hass.config_entries.async_forward_entry_setups(entry, [Platform.WEATHER])
    except BaseException:
        del entry.runtime_data
        await coordinator.async_shutdown()
        raise
    return True


async def async_unload_entry(hass: HomeAssistant, entry: YahooConfigEntry) -> bool:
    """Unload Yahoo! Japan Weather."""
    return await hass.config_entries.async_unload_platforms(entry, [Platform.WEATHER])
