from __future__ import annotations

import unittest
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
            "雨か雪": "snowy-rainy",
            "大雨": "pouring",
            "ひょう": "hail",
            "強風": "windy",
            "強風時々曇り": "windy-variant",
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(map_condition(source), expected)


class YahooPageParsingTests(unittest.TestCase):
    def test_parses_three_hour_forecasts_and_selects_current_slot(self) -> None:
        html = """
        <html><head><script>var TLDataContext = {weather: true};</script>
        <title>江戸川区の天気 - Yahoo!天気・災害</title></head><body>
        <p id="yjw_pinpoint">2026年7月22日　12時00分発表</p>
        <div id="yjw_pinpoint_today">
          <h3>今日の天気 - 7月22日(水)</h3>
          <table><tbody>
            <tr><td>時刻</td><td>12時</td><td>15時</td></tr>
            <tr><td>天気</td><td>晴れ</td><td>晴れ時々曇り</td></tr>
            <tr><td>気温（℃）</td><td>36</td><td>35</td></tr>
            <tr><td>湿度（％）</td><td>65</td><td>68</td></tr>
            <tr><td>降水量（mm）</td><td>0.1</td><td>0.2</td></tr>
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
        self.assertEqual(result.daily[0].precipitation, 0.3)
        self.assertEqual(result.daily[2].datetime, "2026-07-24T00:00:00+09:00")
        self.assertEqual(result.daily[2].condition, "rainy")
        self.assertEqual(result.daily[2].temperature, 33.0)
        self.assertEqual(result.daily[2].temperature_low, 26.0)
        self.assertEqual(result.daily[2].precipitation_probability, 50.0)

    def test_parses_header_cells_normalized_labels_and_compound_wind(self) -> None:
        html = """
        <html><head><title>江戸川区の天気 - Yahoo!天気・災害</title></head><body>
        <p id="yjw_pinpoint">2026年7月22日　12時00分発表</p>
        <div id="yjw_pinpoint_today">
          <h3>今日の天気 - 7月22日(水)</h3>
          <table><tbody>
            <tr><th>時刻</th><td>12時</td><td>15時</td></tr>
            <tr><th>天気</th><td>晴れ</td><td>曇り</td></tr>
            <tr><th>気温 (℃)</th><td>36</td><td>35</td></tr>
            <tr><th>湿度 (％)</th><td>60</td><td>65</td></tr>
            <tr><th>風向 風速 (m/s)</th><td>南 3</td><td>静穏</td></tr>
          </tbody></table>
        </div>
        </body></html>
        """
        now = datetime(2026, 7, 22, 12, 0, tzinfo=ZoneInfo("Asia/Tokyo"))

        result = parse_weather_html(html, now=now)

        self.assertEqual(result.hourly[0].temperature, 36.0)
        self.assertEqual(result.hourly[0].humidity, 60.0)
        self.assertEqual(result.hourly[0].wind_bearing, 180.0)
        self.assertEqual(result.hourly[0].wind_speed, 3.0)
        self.assertIsNone(result.hourly[1].wind_bearing)
        self.assertEqual(result.hourly[1].wind_speed, 0.0)

    def test_rejects_forecast_without_usable_weather_fields(self) -> None:
        html = """
        <html><head><title>江戸川区の天気 - Yahoo!天気・災害</title></head><body>
        <p id="yjw_pinpoint">2026年7月22日　12時00分発表</p>
        <div id="yjw_pinpoint_today">
          <h3>今日の天気 - 7月22日(水)</h3>
          <table><tbody>
            <tr><td>時刻</td><td>12時</td></tr>
            <tr><td>湿度（％）</td><td>65</td></tr>
          </tbody></table>
        </div>
        </body></html>
        """
        now = datetime(2026, 7, 22, 12, 0, tzinfo=ZoneInfo("Asia/Tokyo"))

        with self.assertRaisesRegex(ValueError, "usable"):
            parse_weather_html(html, now=now)

    def test_rejects_out_of_range_weather_values(self) -> None:
        html = """
        <html><head><title>江戸川区の天気 - Yahoo!天気・災害</title></head><body>
        <p id="yjw_pinpoint">2026年7月22日　12時00分発表</p>
        <div id="yjw_pinpoint_today">
          <h3>今日の天気 - 7月22日(水)</h3>
          <table><tbody>
            <tr><td>時刻</td><td>12時</td></tr>
            <tr><td>天気</td><td>晴れ</td></tr>
            <tr><td>気温（℃）</td><td>999</td></tr>
          </tbody></table>
        </div>
        </body></html>
        """
        now = datetime(2026, 7, 22, 12, 0, tzinfo=ZoneInfo("Asia/Tokyo"))

        with self.assertRaisesRegex(ValueError, "range"):
            parse_weather_html(html, now=now)

    def test_rejects_page_without_publication_timestamp(self) -> None:
        html = """
        <html><head><title>江戸川区の天気 - Yahoo!天気・災害</title></head><body>
        <div id="yjw_pinpoint_today">
          <h3>今日の天気 - 7月22日(水)</h3>
          <table><tbody>
            <tr><td>時刻</td><td>12時</td></tr>
            <tr><td>天気</td><td>晴れ</td></tr>
          </tbody></table>
        </div>
        </body></html>
        """
        now = datetime(2026, 7, 22, 12, 0, tzinfo=ZoneInfo("Asia/Tokyo"))

        with self.assertRaisesRegex(ValueError, "publication"):
            parse_weather_html(html, now=now)

    def test_rejects_stale_weather_page(self) -> None:
        html = """
        <html><head><title>江戸川区の天気 - Yahoo!天気・災害</title></head><body>
        <p id="yjw_pinpoint">2025年1月1日　12時00分発表</p>
        <div id="yjw_pinpoint_today">
          <h3>今日の天気 - 1月1日(水)</h3>
          <table><tbody>
            <tr><td>時刻</td><td>12時</td></tr>
            <tr><td>天気</td><td>晴れ</td></tr>
            <tr><td>気温（℃）</td><td>12</td></tr>
          </tbody></table>
        </div>
        </body></html>
        """
        now = datetime(2026, 7, 22, 12, 0, tzinfo=ZoneInfo("Asia/Tokyo"))

        with self.assertRaisesRegex(ValueError, "stale"):
            parse_weather_html(html, now=now)

    def test_ignores_script_and_style_text(self) -> None:
        html = """
        <html><head>
          <script>const fake = "2099年1月1日 00時00分発表";</script>
          <style>.fake::after { content: "2098年1月1日 00時00分発表"; }</style>
          <title>江戸川区の天気 - Yahoo!天気・災害</title>
        </head><body>
        <p id="yjw_pinpoint">2026年7月22日　12時00分発表</p>
        <div id="yjw_pinpoint_today">
          <h3>今日の天気 - 7月22日(水)</h3>
          <table><tbody>
            <tr><td>時刻</td><td>12時</td></tr>
            <tr><td>天気</td><td>晴れ</td></tr>
            <tr><td>気温（℃）</td><td>36</td></tr>
          </tbody></table>
        </div>
        </body></html>
        """

        result = parse_weather_html(
            html,
            now=datetime(2026, 7, 22, 12, 0, tzinfo=ZoneInfo("Asia/Tokyo")),
        )

        self.assertEqual(result.published_at, "2026-07-22T12:00:00+09:00")
        self.assertEqual(result.hourly[0].datetime, "2026-07-22T12:00:00+09:00")

    def test_ignores_tables_after_weather_section(self) -> None:
        html = """
        <html><head><title>江戸川区の天気 - Yahoo!天気・災害</title></head><body>
        <p id="yjw_pinpoint">2026年7月22日　12時00分発表</p>
        <div id="yjw_pinpoint_today">
          <h3>今日の天気 - 7月22日(水)</h3>
          <table><tbody>
            <tr><td>時刻</td><td>12時</td></tr>
            <tr><td>天気</td><td>晴れ</td></tr>
            <tr><td>気温（℃）</td><td>36</td></tr>
            <tr><td>風向<br>風速（m/s）</td><td>南<br>3</td></tr>
          </tbody></table>
        </div>
        <table><tbody>
          <tr><td>時刻</td><td>99時</td></tr>
          <tr><td>天気</td><td>偽データ</td></tr>
        </tbody></table>
        </body></html>
        """

        result = parse_weather_html(
            html,
            now=datetime(2026, 7, 22, 12, 0, tzinfo=ZoneInfo("Asia/Tokyo")),
        )

        self.assertEqual(len(result.hourly), 1)
        self.assertEqual(result.hourly[0].temperature, 36.0)

    def test_rejects_when_all_hourly_slots_are_expired(self) -> None:
        html = """
        <html><head><title>江戸川区の天気 - Yahoo!天気・災害</title></head><body>
        <div id="yjw_pinpoint">
          <p>2026年7月22日　12時00分発表</p>
          <div id="yjw_pinpoint_today">
            <h3>今日の天気 - 7月20日(月)</h3>
            <table><tbody>
              <tr><td>時刻</td><td>12時</td><td>15時</td></tr>
              <tr><td>天気</td><td>晴れ</td><td>曇り</td></tr>
              <tr><td>気温（℃）</td><td>30</td><td>29</td></tr>
            </tbody></table>
          </div>
        </div>
        </body></html>
        """
        now = datetime(2026, 7, 22, 12, 0, tzinfo=ZoneInfo("Asia/Tokyo"))

        with self.assertRaisesRegex(ValueError, "expired"):
            parse_weather_html(html, now=now)

    def test_rejects_out_of_range_weekly_values(self) -> None:
        now = datetime(2026, 7, 22, 12, 0, tzinfo=ZoneInfo("Asia/Tokyo"))
        cases = (("999<br>20", "50"), ("30<br>20", "999"))
        for temperatures, probability in cases:
            with self.subTest(temperatures=temperatures, probability=probability):
                html = f"""
                <html><head>
                <title>江戸川区の天気 - Yahoo!天気・災害</title></head><body>
                <div id="yjw_pinpoint">
                  <p>2026年7月22日　12時00分発表</p>
                  <div id="yjw_pinpoint_today">
                    <h3>今日の天気 - 7月22日(水)</h3>
                    <table><tbody>
                      <tr><td>時刻</td><td>12時</td></tr>
                      <tr><td>天気</td><td>晴れ</td></tr>
                      <tr><td>気温（℃）</td><td>30</td></tr>
                    </tbody></table>
                  </div>
                </div>
                <div id="yjw_week"><table><tbody>
                  <tr><td>日付</td><td>7月24日(金)</td></tr>
                  <tr><td>天気</td><td>晴れ</td></tr>
                  <tr><td>気温（℃）</td><td>{temperatures}</td></tr>
                  <tr><td>降水確率（％）</td><td>{probability}</td></tr>
                </tbody></table></div>
                </body></html>
                """

                with self.assertRaisesRegex(ValueError, "range"):
                    parse_weather_html(html, now=now)

    def test_uses_publication_timestamp_from_pinpoint_container(self) -> None:
        html = """
        <html><head><title>江戸川区の天気 - Yahoo!天気・災害</title></head><body>
        <aside>2026年7月22日　12時00分発表</aside>
        <div id="yjw_pinpoint">
          <p class="yjSt yjw_note_h2">2025年1月1日　12時00分発表</p>
          <div id="yjw_pinpoint_today">
            <h3>今日の天気 - 7月22日(水)</h3>
            <table><tbody>
              <tr><td>時刻</td><td>12時</td></tr>
              <tr><td>天気</td><td>晴れ</td></tr>
              <tr><td>気温（℃）</td><td>30</td></tr>
            </tbody></table>
          </div>
        </div>
        </body></html>
        """
        now = datetime(2026, 7, 22, 12, 0, tzinfo=ZoneInfo("Asia/Tokyo"))

        with self.assertRaisesRegex(ValueError, "stale"):
            parse_weather_html(html, now=now)

    def test_rejects_hourly_slots_beyond_forecast_horizon(self) -> None:
        html = """
        <html><head><title>江戸川区の天気 - Yahoo!天気・災害</title></head><body>
        <div id="yjw_pinpoint">
          <p>2026年7月22日　12時00分発表</p>
          <div id="yjw_pinpoint_today">
            <h3>今日の天気 - 7月31日(金)</h3>
            <table><tbody>
              <tr><td>時刻</td><td>12時</td></tr>
              <tr><td>天気</td><td>晴れ</td></tr>
              <tr><td>気温（℃）</td><td>30</td></tr>
            </tbody></table>
          </div>
        </div>
        </body></html>
        """
        now = datetime(2026, 7, 22, 12, 0, tzinfo=ZoneInfo("Asia/Tokyo"))

        with self.assertRaisesRegex(ValueError, "horizon"):
            parse_weather_html(html, now=now)


if __name__ == "__main__":
    unittest.main()
