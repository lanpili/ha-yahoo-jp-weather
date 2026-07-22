from __future__ import annotations

import pytest
from homeassistant import config_entries
from homeassistant.const import CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.yahoo_jp_weather.config_flow import (
    CONF_MUNICIPALITY,
    CONF_PREFECTURE,
)
from custom_components.yahoo_jp_weather.const import (
    CONF_ENTITY_UNIQUE_ID,
    CONF_NAME,
    DOMAIN,
)
from tests.helpers import weather_html

OLD_URL = "https://weather.yahoo.co.jp/weather/jp/13/4410/13123.html"
NEW_URL = "https://weather.yahoo.co.jp/weather/jp/13/4410/13101.html"
PREFECTURE_URL = "https://weather.yahoo.co.jp/weather/jp/13/"
AREA_URL = "https://weather.yahoo.co.jp/weather/jp/13/4410.html"

PREFECTURE_HTML = '<a href="/weather/jp/13/4410.html">東京地方</a>'
AREA_HTML = '<a href="/weather/jp/13/4410/13101.html">千代田区</a>'


def make_entry() -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        title="江戸川区",
        unique_id="13123",
        version=2,
        data={
            CONF_NAME: "江戸川区",
            CONF_URL: OLD_URL,
            CONF_ENTITY_UNIQUE_ID: "13123",
        },
    )


async def start_user(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> dict:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    aioclient_mock.get(PREFECTURE_URL, text=PREFECTURE_HTML)
    aioclient_mock.get(AREA_URL, text=AREA_HTML)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PREFECTURE: "13"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "municipality"
    return result


async def start_reconfigure(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    entry: MockConfigEntry,
) -> dict:
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "entry_id": entry.entry_id,
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    aioclient_mock.get(PREFECTURE_URL, text=PREFECTURE_HTML)
    aioclient_mock.get(AREA_URL, text=AREA_HTML)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PREFECTURE: "13"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "municipality"
    return result


@pytest.mark.asyncio
async def test_reconfigure_rejects_invalid_weather_page_atomically(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    entry = make_entry()
    entry.add_to_hass(hass)
    original_data = dict(entry.data)
    result = await start_reconfigure(hass, aioclient_mock, entry)
    aioclient_mock.get(NEW_URL, text="<html>not a weather page</html>")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_MUNICIPALITY: "13101"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "municipality"
    assert result["errors"] == {"base": "invalid_weather"}
    assert entry.data == original_data
    assert entry.title == "江戸川区"
    assert entry.unique_id == "13123"


@pytest.mark.asyncio
async def test_reconfigure_validates_then_preserves_entity_unique_id(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    entry = make_entry()
    entry.add_to_hass(hass)
    result = await start_reconfigure(hass, aioclient_mock, entry)
    aioclient_mock.get(NEW_URL, text=weather_html(area="千代田区"))

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_MUNICIPALITY: "13101"}
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.data[CONF_URL] == NEW_URL
    assert entry.data[CONF_ENTITY_UNIQUE_ID] == "13123"
    assert entry.title == "千代田区"
    assert entry.unique_id == "13101"
    if entry.state is config_entries.ConfigEntryState.LOADED:
        assert await hass.config_entries.async_unload(entry.entry_id)


@pytest.mark.asyncio
async def test_user_flow_validates_and_creates_entry(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    result = await start_user(hass, aioclient_mock)
    aioclient_mock.get(NEW_URL, text=weather_html(area="千代田区"))

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_MUNICIPALITY: "13101"}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "千代田区"
    assert result["data"][CONF_URL] == NEW_URL
    assert result["data"][CONF_ENTITY_UNIQUE_ID] == "13101"


@pytest.mark.asyncio
async def test_user_flow_aborts_duplicate_location(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    duplicate = MockConfigEntry(
        domain=DOMAIN,
        title="千代田区",
        unique_id="13101",
        version=2,
        data={
            CONF_NAME: "千代田区",
            CONF_URL: NEW_URL,
            CONF_ENTITY_UNIQUE_ID: "13101",
        },
    )
    duplicate.add_to_hass(hass)
    result = await start_user(hass, aioclient_mock)
    aioclient_mock.get(NEW_URL, text=weather_html(area="千代田区"))

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_MUNICIPALITY: "13101"}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


@pytest.mark.asyncio
async def test_user_flow_reports_connection_failure(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    aioclient_mock.get(PREFECTURE_URL, status=503)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PREFECTURE: "13"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}
