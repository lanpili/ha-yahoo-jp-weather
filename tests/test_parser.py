from __future__ import annotations

import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
custom_components = types.ModuleType("custom_components")
custom_components.__path__ = [str(ROOT / "custom_components")]
component = types.ModuleType("custom_components.yahoo_jp_weather")
component.__path__ = [str(ROOT / "custom_components" / "yahoo_jp_weather")]
sys.modules.setdefault("custom_components", custom_components)
sys.modules.setdefault("custom_components.yahoo_jp_weather", component)

from datetime import datetime
from zoneinfo import ZoneInfo

from custom_components.yahoo_jp_weather.parser import map_condition, parse_weather_html


class ConditionMappingTests(unittest.TestCase):
    def test_maps_common_yahoo_japan_conditions(self) -> None:
        cases = {
            "晴れ": "sunny",
            "曇り": "cloudy",
            "晴れ時々曇り": "partlycloudy",
            "雨": "rainy",
            "雷雨": "lightning-rainy",
            "雪": "snowy",
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(map_condition(source), expected)


class YahooPageParsingTests(unittest.TestCase):
    def test_parses_three_hour_forecasts_and_selects_current_slot(self) -> None:
        html = """
        <html><head><script>var TLDataContext = {weather: true};</script>
        <title>江戸川区の天気 - Yahoo!天気・災害</title></head><body>
        <p>2026年7月22日　12時00分発表</p>
        <div id="yjw_pinpoint_today">
          <h3>今日の天気 - 7月22日(水)</h3>
          <table><tbody>
            <tr><td>時刻</td><td>12時</td><td>15時</td></tr>
            <tr><td>天気</td><td>晴れ</td><td>晴れ時々曇り</td></tr>
            <tr><td>気温（℃）</td><td>36</td><td>35</td></tr>
            <tr><td>湿度（％）</td><td>65</td><td>68</td></tr>
            <tr><td>降水量（mm）</td><td>0.1</td><td>0</td></tr>
            <tr><td>風向<br>風速（m/s）</td><td>南南東<br>4</td><td>南<br>3</td></tr>
          </tbody></table>
        </div>
        <div id="yjw_pinpoint_tomorrow">
          <h3>明日の天気 - 7月23日(木)</h3>
          <table><tbody>
            <tr><td>時刻</td><td>0時</td><td>3時</td></tr>
            <tr><td>天気</td><td>曇り</td><td>雨</td></tr>
            <tr><td>気温（℃）</td><td>29</td><td>28</td></tr>
            <tr><td>湿度（％）</td><td>80</td><td>85</td></tr>
            <tr><td>降水量（mm）</td><td>0</td><td>1.5</td></tr>
            <tr><td>風向<br>風速（m/s）</td><td>南<br>2</td><td>北<br>1</td></tr>
          </tbody></table>
        </div>
        <div id="yjw_week">
          <table><tbody>
            <tr><td>日付</td><td>7月24日<br>(金)</td><td>7月25日<br>(土)</td></tr>
            <tr><td>天気</td><td>曇のち雨</td><td>曇時々晴</td></tr>
            <tr><td>気温（℃）</td><td>33<br>26</td><td>34<br>25</td></tr>
            <tr><td>降水<br>確率（％）</td><td>50</td><td>30</td></tr>
          </tbody></table>
        </div></body></html>
        """
        now = datetime(2026, 7, 22, 12, 30, tzinfo=ZoneInfo("Asia/Tokyo"))

        result = parse_weather_html(html, now=now)

        self.assertEqual(result.area_name, "江戸川区")
        self.assertEqual(result.published_at, "2026-07-22T12:00:00+09:00")
        self.assertEqual(len(result.hourly), 4)
        self.assertEqual(result.hourly[0].datetime, "2026-07-22T12:00:00+09:00")
        self.assertEqual(result.hourly[0].condition, "sunny")
        self.assertEqual(result.hourly[0].temperature, 36.0)
        self.assertEqual(result.hourly[0].humidity, 65.0)
        self.assertEqual(result.hourly[0].precipitation, 0.1)
        self.assertEqual(result.hourly[0].wind_bearing, 157.5)
        self.assertEqual(result.hourly[0].wind_speed, 4.0)
        self.assertEqual(result.hourly[-1].datetime, "2026-07-23T03:00:00+09:00")
        self.assertEqual(result.current.datetime, result.hourly[0].datetime)
        self.assertEqual(len(result.daily), 4)
        self.assertEqual(result.daily[0].temperature, 36.0)
        self.assertEqual(result.daily[0].temperature_low, 35.0)
        self.assertEqual(result.daily[2].datetime, "2026-07-24T00:00:00+09:00")
        self.assertEqual(result.daily[2].condition, "rainy")
        self.assertEqual(result.daily[2].temperature, 33.0)
        self.assertEqual(result.daily[2].temperature_low, 26.0)
        self.assertEqual(result.daily[2].precipitation_probability, 50.0)


if __name__ == "__main__":
    unittest.main()
