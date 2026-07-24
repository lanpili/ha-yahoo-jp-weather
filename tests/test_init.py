from __future__ import annotations

from unittest.mock import patch

import pytest
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_URL
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.yahoo_jp_weather import CONFIG_SCHEMA, async_migrate_entry
from custom_components.yahoo_jp_weather.const import (
    CONF_ENTITY_UNIQUE_ID,
    CONF_NAME,
    DOMAIN,
)
from custom_components.yahoo_jp_weather.coordinator import YahooJapanWeatherCoordinator
from custom_components.yahoo_jp_weather.diagnostics import (
    async_get_config_entry_diagnostics,
)
from tests.helpers import weather_api_json

URL = "https://weather.yahoo.co.jp/weather/jp/13/4410/13123.html"
API_URL = (
    "https://weather.yahooapis.jp/Weather/V1/getCityDays?"
    "date=week&hours=onehourand3&jis=13123&output=json&precipdecimal=1&v=2"
)


def make_entry(*, version: int = 1) -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        title="江戸川区",
        unique_id="13123",
        version=version,
        data={
            CONF_NAME: "江戸川区",
            CONF_URL: URL,
            CONF_ENTITY_UNIQUE_ID: "13123",
        },
    )


@pytest.mark.asyncio
async def test_setup_and_unload_use_config_entry_runtime_data(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    entry = make_entry()
    entry.add_to_hass(hass)
    aioclient_mock.get(API_URL, text=weather_api_json())

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert isinstance(entry.runtime_data, YahooJapanWeatherCoordinator)
    weather_states = hass.states.async_all("weather")
    assert len(weather_states) == 1
    entity_id = weather_states[0].entity_id
    assert "source_url" not in weather_states[0].attributes
    assert weather_states[0].attributes["forecast_interval_hours"] == 1

    hourly = await hass.services.async_call(
        "weather",
        "get_forecasts",
        {"entity_id": entity_id, "type": "hourly"},
        blocking=True,
        return_response=True,
    )
    daily = await hass.services.async_call(
        "weather",
        "get_forecasts",
        {"entity_id": entity_id, "type": "daily"},
        blocking=True,
        return_response=True,
    )
    assert hourly[entity_id]["forecast"]
    assert daily[entity_id]["forecast"]

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert getattr(entry, "runtime_data", None) is None


@pytest.mark.asyncio
async def test_first_refresh_failure_schedules_retry_without_stale_state(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    entry = make_entry(version=2)
    entry.add_to_hass(hass)
    aioclient_mock.get(API_URL, status=503)

    assert not await hass.config_entries.async_setup(entry.entry_id)

    assert entry.state is config_entries.ConfigEntryState.SETUP_RETRY
    assert getattr(entry, "runtime_data", None) is None
    assert hass.states.async_all("weather") == []


@pytest.mark.asyncio
async def test_platform_setup_failure_clears_runtime_data(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    entry = make_entry()
    entry.add_to_hass(hass)
    aioclient_mock.get(API_URL, text=weather_api_json())

    with patch.object(
        hass.config_entries,
        "async_forward_entry_setups",
        side_effect=RuntimeError("platform failed"),
    ):
        assert not await hass.config_entries.async_setup(entry.entry_id)

    assert getattr(entry, "runtime_data", None) is None


@pytest.mark.asyncio
async def test_migrates_legacy_entry_to_version_two(hass: HomeAssistant) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="江戸川区",
        unique_id="13123",
        version=1,
        data={CONF_NAME: "江戸川区", CONF_URL: f"{URL}?legacy=1#top"},
    )
    entry.add_to_hass(hass)

    assert await async_migrate_entry(hass, entry)

    assert entry.version == 2
    assert entry.data[CONF_URL] == URL
    assert entry.data[CONF_ENTITY_UNIQUE_ID] == "13123"


def test_yaml_schema_rejects_non_yahoo_url() -> None:
    with pytest.raises(vol.Invalid):
        CONFIG_SCHEMA(
            {DOMAIN: {CONF_NAME: "Unsafe", CONF_URL: "http://127.0.0.1/internal"}}
        )


@pytest.mark.asyncio
async def test_diagnostics_are_useful_and_redacted(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    entry = make_entry(version=2)
    entry.add_to_hass(hass)
    aioclient_mock.get(API_URL, text=weather_api_json())
    assert await hass.config_entries.async_setup(entry.entry_id)

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert diagnostics["last_update_success"] is True
    assert diagnostics["last_error_category"] is None
    assert diagnostics["hourly_count"] >= 1
    assert diagnostics["last_successful_update"] is not None
    serialized = str(diagnostics)
    assert URL not in serialized
    assert "江戸川区" not in serialized
