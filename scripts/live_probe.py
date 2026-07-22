"""Low-frequency live Yahoo parser smoke test for scheduled CI."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any
from urllib.request import HTTPRedirectHandler, Request, build_opener

URL = "https://weather.yahoo.co.jp/weather/jp/13/4410/13101.html"
PARSER_PATH = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "yahoo_jp_weather"
    / "parser.py"
)


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


def fetch_html(*, opener: Any | None = None) -> str:
    """Fetch the fixed Yahoo page without following redirects."""
    request = Request(URL, headers={"User-Agent": "HomeAssistant YahooJapanWeather"})
    http = opener or build_opener(_NoRedirectHandler())
    with http.open(request, timeout=20) as response:  # noqa: S310 - fixed URL
        if response.geturl() != URL:
            raise RuntimeError("Live probe rejected a redirected response")
        return response.read().decode("utf-8")


def main() -> None:
    spec = importlib.util.spec_from_file_location(
        "yahoo_jp_weather_parser", PARSER_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load parser module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    html = fetch_html()
    data = module.parse_weather_html(html)
    if not data.hourly or not data.daily:
        raise RuntimeError("Live page parsed without usable forecasts")
    print(
        f"OK: hourly={len(data.hourly)} daily={len(data.daily)} "
        f"published_at={data.published_at}"
    )


if __name__ == "__main__":
    main()
