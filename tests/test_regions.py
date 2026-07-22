from __future__ import annotations

import unittest

from custom_components.yahoo_jp_weather.regions import (
    PREFECTURES,
    parse_forecast_areas,
    parse_location_url,
    parse_municipalities,
    validate_municipality_url,
)


class RegionParserTests(unittest.TestCase):
    def test_parses_location_codes_from_municipality_url(self) -> None:
        self.assertEqual(
            parse_location_url(
                "https://weather.yahoo.co.jp/weather/jp/13/4410/13123.html"
            ),
            ("13", "4410", "13123"),
        )
        self.assertIsNone(parse_location_url("https://example.com/not-yahoo"))

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

    def test_parses_relative_forecast_area_links(self) -> None:
        html = '<a href="4410.html?src=test#forecast">東京</a>'

        result = parse_forecast_areas(html, "13")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].code, "4410")
        self.assertEqual(
            result[0].url,
            "https://weather.yahoo.co.jp/weather/jp/13/4410.html",
        )

    def test_validates_and_canonicalizes_municipality_urls(self) -> None:
        self.assertEqual(
            validate_municipality_url(
                "https://weather.yahoo.co.jp/weather/jp/13/4410/13123.html?src=x#top"
            ),
            "https://weather.yahoo.co.jp/weather/jp/13/4410/13123.html",
        )
        for url in (
            "http://weather.yahoo.co.jp/weather/jp/13/4410/13123.html",
            "https://example.com/weather/jp/13/4410/13123.html",
            "http://127.0.0.1/internal",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                validate_municipality_url(url)


if __name__ == "__main__":
    unittest.main()
