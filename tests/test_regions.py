from __future__ import annotations

import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
custom_components = types.ModuleType("custom_components")
custom_components.__path__ = [str(ROOT / "custom_components")]
component = types.ModuleType("custom_components.yahoo_jp_weather")
component.__path__ = [str(ROOT / "custom_components" / "yahoo_jp_weather")]
sys.modules.setdefault("custom_components", custom_components)
sys.modules.setdefault("custom_components.yahoo_jp_weather", component)

from custom_components.yahoo_jp_weather.regions import (
    PREFECTURES,
    parse_forecast_areas,
    parse_municipalities,
)


class RegionParserTests(unittest.TestCase):
    def test_has_all_japanese_prefectures(self) -> None:
        self.assertEqual(len(PREFECTURES), 47)
        self.assertEqual(PREFECTURES["13"], "東京都")
        self.assertEqual(PREFECTURES["47"], "沖縄県")

    def test_parses_prefecture_forecast_areas(self) -> None:
        html = """
        <a href="https://weather.yahoo.co.jp/weather/jp/13/4410.html">
          東京 <span>36/28</span><span>20%</span>
        </a>
        <a href="https://weather.yahoo.co.jp/weather/jp/13/4420.html">
          大島 <span>32/27</span>
        </a>
        <a href="https://example.com/ignore">Ignore</a>
        """

        result = parse_forecast_areas(html, "13")

        self.assertEqual(
            [(item.code, item.name, item.url) for item in result],
            [
                (
                    "4410",
                    "東京",
                    "https://weather.yahoo.co.jp/weather/jp/13/4410.html",
                ),
                (
                    "4420",
                    "大島",
                    "https://weather.yahoo.co.jp/weather/jp/13/4420.html",
                ),
            ],
        )

    def test_parses_municipalities(self) -> None:
        html = """
        <a href="https://weather.yahoo.co.jp/weather/jp/13/">東京都</a>
        <a href="https://weather.yahoo.co.jp/weather/jp/13/4410/13101.html">千代田区</a>
        <a href="https://weather.yahoo.co.jp/weather/jp/13/4410/13123.html">江戸川区</a>
        """

        result = parse_municipalities(html, "13", "4410")

        self.assertEqual(
            [(item.code, item.name) for item in result],
            [("13101", "千代田区"), ("13123", "江戸川区")],
        )
        self.assertTrue(result[-1].url.endswith("/13/4410/13123.html"))


if __name__ == "__main__":
    unittest.main()
