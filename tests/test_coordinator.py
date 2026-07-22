from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.yahoo_jp_weather.const import CONF_NAME, DOMAIN
from custom_components.yahoo_jp_weather.coordinator import YahooJapanWeatherCoordinator
from tests.helpers import weather_html

URL = "https://weather.yahoo.co.jp/weather/jp/13/4410/13123.html"


def test_coordinator_explicitly_owns_config_entry(hass: HomeAssistant) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="江戸川区",
        unique_id="13123",
        data={CONF_NAME: "江戸川区", "url": URL, "entity_unique_id": "13123"},
    )
    entry.add_to_hass(hass)

    coordinator = YahooJapanWeatherCoordinator(hass, entry)

    assert coordinator.config_entry is entry
    assert coordinator.url == URL


@pytest.mark.asyncio
async def test_coordinator_fetches_and_parses_weather(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="江戸川区",
        unique_id="13123",
        data={CONF_NAME: "江戸川区", "url": URL, "entity_unique_id": "13123"},
    )
    entry.add_to_hass(hass)
    aioclient_mock.get(URL, text=weather_html())
    coordinator = YahooJapanWeatherCoordinator(hass, entry)

    data = await coordinator._async_update_data()

    assert data.area_name == "江戸川区"
    assert data.hourly
    assert coordinator.last_error_category is None
    assert coordinator.last_successful_update is not None


@pytest.mark.asyncio
async def test_coordinator_rejects_cross_host_redirect(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="江戸川区",
        unique_id="13123",
        data={CONF_NAME: "江戸川区", "url": URL, "entity_unique_id": "13123"},
    )
    entry.add_to_hass(hass)
    redirected = "https://example.com/weather.html"
    aioclient_mock.get(URL, status=302, headers={"Location": redirected})
    aioclient_mock.get(redirected, text=weather_html())
    coordinator = YahooJapanWeatherCoordinator(hass, entry)

    with pytest.raises(UpdateFailed, match="redirect"):
        await coordinator._async_update_data()
    assert coordinator.last_error_category == "redirect"


@pytest.mark.asyncio
async def test_coordinator_classifies_http_failure(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="江戸川区",
        unique_id="13123",
        data={CONF_NAME: "江戸川区", "url": URL, "entity_unique_id": "13123"},
    )
    entry.add_to_hass(hass)
    aioclient_mock.get(URL, status=503)
    coordinator = YahooJapanWeatherCoordinator(hass, entry)

    with pytest.raises(UpdateFailed, match="503"):
        await coordinator._async_update_data()
    assert coordinator.last_error_category == "http_503"


@pytest.mark.asyncio
async def test_coordinator_classifies_rate_limit(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="江戸川区",
        unique_id="13123",
        data={CONF_NAME: "江戸川区", "url": URL, "entity_unique_id": "13123"},
    )
    entry.add_to_hass(hass)
    aioclient_mock.get(URL, status=429)
    coordinator = YahooJapanWeatherCoordinator(hass, entry)

    with pytest.raises(UpdateFailed, match="429"):
        await coordinator._async_update_data()
    assert coordinator.last_error_category == "http_429"


@pytest.mark.asyncio
async def test_coordinator_classifies_timeout_and_parse_failure(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="江戸川区",
        unique_id="13123",
        data={CONF_NAME: "江戸川区", "url": URL, "entity_unique_id": "13123"},
    )
    entry.add_to_hass(hass)
    coordinator = YahooJapanWeatherCoordinator(hass, entry)

    aioclient_mock.get(URL, exc=TimeoutError())
    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()
    assert coordinator.last_error_category == "timeout"

    aioclient_mock.clear_requests()
    aioclient_mock.get(URL, text="<html>invalid</html>")
    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()
    assert coordinator.last_error_category == "parse"


@pytest.mark.asyncio
async def test_coordinator_clears_error_after_recovery(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="江戸川区",
        unique_id="13123",
        data={CONF_NAME: "江戸川区", "url": URL, "entity_unique_id": "13123"},
    )
    entry.add_to_hass(hass)
    coordinator = YahooJapanWeatherCoordinator(hass, entry)
    aioclient_mock.get(URL, status=503)
    aioclient_mock.get(URL, text=weather_html())

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()
    aioclient_mock.clear_requests()
    aioclient_mock.get(URL, text=weather_html())
    data = await coordinator._async_update_data()

    assert data.hourly
    assert coordinator.last_error_category is None
    assert coordinator.last_successful_update is not None
