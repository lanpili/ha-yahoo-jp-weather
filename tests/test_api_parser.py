from __future__ import annotations

import json
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from custom_components.yahoo_jp_weather.api_parser import parse_weather_api


class YahooAppApiParsingTests(unittest.TestCase):
    @staticmethod
    def _minimal_payload() -> dict[str, object]:
        return {
            "ResultSet": {
                "Result": [
                    {
                        "JisName": "江戸川区",
                        "Day": [
                            {
                                "Date": "2026-07-24",
                                "RefTime": "2026-07-24T11:00:00+09:00",
                                "Weather": {"Code": "100", "Telop": "晴れ"},
                                "Temp": {"Min": "26", "Max": "34"},
                                "Precip": "20",
                                "Hour": [
                                    {
                                        "Time": "2026-07-24T12:00:00+09:00",
                                        "Weather": {"Code": "11", "Telop": "晴れ"},
                                        "ProbPrecip": "20",
                                        "Temp": "34",
                                    }
                                ],
                            }
                        ],
                    }
                ]
            }
        }

    def test_rejects_non_object_nested_structures_as_value_error(self) -> None:
        for target in (
            "daily_weather",
            "daily_temp",
            "hourly_weather",
            "hourly_precipitation",
            "hourly_wind_speed",
            "hourly_wind_direction",
        ):
            payload = self._minimal_payload()
            day = payload["ResultSet"]["Result"][0]["Day"][0]  # type: ignore[index]
            if target == "daily_weather":
                day["Weather"] = "晴れ"
            elif target == "daily_temp":
                day["Temp"] = "34"
            elif target == "hourly_weather":
                day["Hour"][0]["Weather"] = "晴れ"
            elif target == "hourly_precipitation":
                day["Hour"][0]["Precip"] = []
            elif target == "hourly_wind_speed":
                day["Hour"][0]["WindSpeed"] = []
            else:
                day["Hour"][0]["WindDirection"] = []

            with self.subTest(target=target), self.assertRaises(ValueError):
                parse_weather_api(
                    json.dumps(payload),
                    now=datetime(2026, 7, 24, 12, 0, tzinfo=ZoneInfo("Asia/Tokyo")),
                )

    def test_rejects_timezone_naive_timestamps(self) -> None:
        for target in ("RefTime", "Time"):
            payload = self._minimal_payload()
            day = payload["ResultSet"]["Result"][0]["Day"][0]  # type: ignore[index]
            if target == "RefTime":
                day["RefTime"] = "2026-07-24T11:00:00"
            else:
                day["Hour"][0]["Time"] = "2026-07-24T12:00:00"

            with (
                self.subTest(target=target),
                self.assertRaisesRegex(ValueError, "timezone"),
            ):
                parse_weather_api(
                    json.dumps(payload),
                    now=datetime(2026, 7, 24, 12, 0, tzinfo=ZoneInfo("Asia/Tokyo")),
                )

    def test_caps_daily_forecasts_at_ten_days(self) -> None:
        payload = self._minimal_payload()
        first_day = payload["ResultSet"]["Result"][0]["Day"][0]  # type: ignore[index]
        days = []
        for offset in range(12):
            day = json.loads(json.dumps(first_day))
            date = datetime(2026, 7, 24, tzinfo=ZoneInfo("Asia/Tokyo"))
            date = (
                date.replace(day=24 + offset)
                if offset < 8
                else datetime(2026, 8, offset - 7, tzinfo=ZoneInfo("Asia/Tokyo"))
            )
            day["Date"] = date.date().isoformat()
            day["Hour"][0]["Time"] = date.replace(hour=12).isoformat()
            days.append(day)
        payload["ResultSet"]["Result"][0]["Day"] = days  # type: ignore[index]

        data = parse_weather_api(
            json.dumps(payload),
            now=datetime(2026, 7, 24, 12, 0, tzinfo=ZoneInfo("Asia/Tokyo")),
        )

        self.assertEqual(len(data.daily), 10)

    def test_parses_true_hourly_probability_and_thunder_code(self) -> None:
        payload = {
            "ResultSet": {
                "Result": [
                    {
                        "JisCode": "13123",
                        "JisName": "江戸川区",
                        "Day": [
                            {
                                "Date": "2026-07-24",
                                "RefTime": "2026-07-24T11:00:00+09:00",
                                "Weather": {"Code": "240", "Telop": "曇時々雨"},
                                "Temp": {"Min": "26", "Max": "34"},
                                "Precip": "50",
                                "Hour": [
                                    {
                                        "Time": "2026-07-24T15:00:00+09:00",
                                        "RefTime": "2026-07-24T11:00:00+09:00",
                                        "Weather": {"Code": "31", "Telop": "曇り"},
                                        "Precip": {"@unit": "mm/h", "0": "0.3"},
                                        "ProbPrecip": "40",
                                        "WindSpeed": {"@unit": "m/s", "0": "2"},
                                        "WindDirection": {"Code": "5", "Name": "南東"},
                                        "Temp": "32",
                                        "Humidity": "68",
                                    },
                                    {
                                        "Time": "2026-07-24T16:00:00+09:00",
                                        "RefTime": "2026-07-24T11:00:00+09:00",
                                        "Weather": {"Code": "54", "Telop": "雨"},
                                        "Precip": {"@unit": "mm/h", "0": "0.4"},
                                        "ProbPrecip": "50",
                                        "WindSpeed": {"@unit": "m/s", "0": "2"},
                                        "WindDirection": {"Code": "5", "Name": "南東"},
                                        "Temp": "32",
                                        "Humidity": "72",
                                    },
                                ],
                            }
                        ],
                    }
                ]
            }
        }

        data = parse_weather_api(
            json.dumps(payload),
            now=datetime(2026, 7, 24, 15, 30, tzinfo=ZoneInfo("Asia/Tokyo")),
        )

        self.assertEqual(data.area_name, "江戸川区")
        self.assertEqual(data.published_at, "2026-07-24T11:00:00+09:00")
        self.assertEqual(len(data.hourly), 2)
        self.assertEqual(data.hourly[1].condition, "lightning-rainy")
        self.assertEqual(data.hourly[1].precipitation_probability, 50.0)
        self.assertEqual(data.hourly[1].precipitation, 0.4)
        self.assertEqual(data.hourly[1].temperature, 32.0)
        self.assertEqual(data.hourly[1].humidity, 72.0)
        self.assertEqual(data.hourly[1].wind_bearing, 135.0)
        self.assertEqual(data.hourly[1].wind_speed, 2.0)
        self.assertEqual(data.daily[0].condition, "lightning-rainy")
        self.assertEqual(data.daily[0].precipitation_probability, 50.0)

    def test_rejects_out_of_range_probability(self) -> None:
        payload = {
            "ResultSet": {
                "Result": [
                    {
                        "JisName": "江戸川区",
                        "Day": [
                            {
                                "Date": "2026-07-24",
                                "RefTime": "2026-07-24T11:00:00+09:00",
                                "Weather": {"Code": "100", "Telop": "晴れ"},
                                "Temp": {"Min": "26", "Max": "34"},
                                "Precip": "20",
                                "Hour": [
                                    {
                                        "Time": "2026-07-24T12:00:00+09:00",
                                        "Weather": {"Code": "11", "Telop": "晴れ"},
                                        "ProbPrecip": "999",
                                        "Temp": "34",
                                    }
                                ],
                            }
                        ],
                    }
                ]
            }
        }

        with self.assertRaisesRegex(ValueError, "probability"):
            parse_weather_api(
                json.dumps(payload),
                now=datetime(2026, 7, 24, 12, 0, tzinfo=ZoneInfo("Asia/Tokyo")),
            )


if __name__ == "__main__":
    unittest.main()
