"""Low-frequency live Yahoo page and App forecast smoke tests for scheduled CI."""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
COMPONENT_PATH = ROOT / "custom_components" / "yahoo_jp_weather"
PAGE_URL = "https://weather.yahoo.co.jp/weather/jp/13/4410/13101.html"
PARSER_PATH = COMPONENT_PATH / "parser.py"
API_PARSER_PATH = COMPONENT_PATH / "api_parser.py"
CONST_PATH = COMPONENT_PATH / "const.py"


def _load_module(name: str, path: Path) -> types.ModuleType:
    """Load a source module without importing Home Assistant dependencies."""
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {path.name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_const = _load_module("yahoo_jp_weather_probe_const", CONST_PATH)
API_QUERY = urlencode(
    {
        "date": "week",
        "hours": "onehourand3",
        "jis": "13101",
        "output": "json",
        "precipdecimal": "1",
        "v": "2",
    }
)
API_URL = f"{_const.APP_API_URL}?{API_QUERY}"
APP_API_USER_AGENT: str = _const.APP_API_USER_AGENT
USER_AGENT: str = _const.USER_AGENT


class _NoRedirectHandler(HTTPRedirectHandler):
    """Reject redirects so the probe matches the integration's fetch policy."""

    def redirect_request(
        self,
        req: Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> None:
        return None


def _fetch(url: str, user_agent: str, *, opener: Any | None = None) -> str:
    """Fetch a fixed Yahoo endpoint without following redirects."""
    request = Request(url, headers={"User-Agent": user_agent})
    http = opener or build_opener(_NoRedirectHandler())
    with http.open(request, timeout=20) as response:  # noqa: S310 - fixed URLs
        if response.geturl() != url:
            raise RuntimeError("Live probe rejected a redirected response")
        return response.read().decode("utf-8")


def fetch_html(*, opener: Any | None = None) -> str:
    """Fetch the fixed Yahoo municipality page."""
    return _fetch(PAGE_URL, USER_AGENT, opener=opener)


def fetch_api(*, opener: Any | None = None) -> str:
    """Fetch the fixed Yahoo App one-hour forecast response."""
    return _fetch(API_URL, APP_API_USER_AGENT, opener=opener)


def _load_parsers() -> tuple[types.ModuleType, types.ModuleType]:
    """Load parser modules inside a synthetic package for relative imports."""
    package_name = "yahoo_jp_weather_probe"
    package = types.ModuleType(package_name)
    package.__path__ = [str(COMPONENT_PATH)]  # type: ignore[attr-defined]
    sys.modules[package_name] = package
    parser = _load_module(f"{package_name}.parser", PARSER_PATH)
    api_parser = _load_module(f"{package_name}.api_parser", API_PARSER_PATH)
    return parser, api_parser


def main() -> None:
    parser, api_parser = _load_parsers()

    page_data = parser.parse_weather_html(fetch_html())
    if not page_data.hourly or not page_data.daily:
        raise RuntimeError("Live page parsed without usable forecasts")

    api_data = api_parser.parse_weather_api(fetch_api())
    if not api_data.hourly or not api_data.daily:
        raise RuntimeError("Live App response parsed without usable forecasts")
    if not any(item.precipitation_probability is not None for item in api_data.hourly):
        raise RuntimeError("Live App response omitted hourly precipitation probability")

    print(
        f"OK: page_hourly={len(page_data.hourly)} page_daily={len(page_data.daily)} "
        f"api_hourly={len(api_data.hourly)} api_daily={len(api_data.daily)} "
        f"published_at={api_data.published_at}"
    )


if __name__ == "__main__":
    main()
