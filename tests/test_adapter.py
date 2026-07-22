from __future__ import annotations

import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from custom_components.yahoo_jp_weather.adapter import (
    daily_forecasts_for_ha,
    hourly_forecasts_for_ha,
)
from custom_components.yahoo_jp_weather.parser import (
    DailyForecast,
    HourlyForecast,
)


class HomeAssistantAdapterTests(unittest.TestCase):
    def test_filters_old_slots_and_keeps_native_values(self) -> None:
        slots = [
            HourlyForecast(
                datetime="2026-07-22T09:00:00+09:00",
                condition="sunny",
                temperature=33.0,
                humidity=70.0,
                precipitation=0.0,
                wind_bearing=180.0,
                wind_speed=2.0,
            ),
            HourlyForecast(
                datetime="2026-07-22T12:00:00+09:00",
                condition="partlycloudy",
                temperature=35.0,
                humidity=68.0,
                precipitation=0.1,
                wind_bearing=157.5,
                wind_speed=4.0,
            ),
            HourlyForecast(
                datetime="2026-07-22T15:00:00+09:00",
                condition=None,
                temperature=None,
                humidity=72.0,
                precipitation=0.0,
                wind_bearing=90.0,
                wind_speed=1.0,
            ),
        ]
        now = datetime(2026, 7, 22, 12, 30, tzinfo=ZoneInfo("Asia/Tokyo"))

        result = hourly_forecasts_for_ha(slots, now=now)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["datetime"], "2026-07-22T12:00:00+09:00")
        self.assertEqual(result[0]["native_temperature"], 35.0)
        self.assertEqual(result[0]["humidity"], 68.0)
        self.assertEqual(result[0]["native_precipitation"], 0.1)
        self.assertEqual(result[0]["native_wind_speed"], 4.0)

    def test_converts_daily_native_values(self) -> None:
        days = [
            DailyForecast(
                datetime="2026-07-22T00:00:00+09:00",
                condition="sunny",
                temperature=36.0,
                temperature_low=29.0,
                precipitation=0.3,
            )
        ]

        now = datetime(2026, 7, 22, 12, 0, tzinfo=ZoneInfo("Asia/Tokyo"))
        result = daily_forecasts_for_ha(days, now=now)

        self.assertEqual(
            result[0],
            {
                "datetime": "2026-07-22T00:00:00+09:00",
                "condition": "sunny",
                "native_temperature": 36.0,
                "native_templow": 29.0,
                "native_precipitation": 0.3,
            },
        )

    def test_filters_expired_daily_forecasts(self) -> None:
        days = [
            DailyForecast(
                datetime="2026-07-21T00:00:00+09:00",
                condition="rainy",
                temperature=None,
                temperature_low=None,
                precipitation=None,
            ),
            DailyForecast(
                datetime="2026-07-22T00:00:00+09:00",
                condition="sunny",
                temperature=None,
                temperature_low=None,
                precipitation=None,
            ),
        ]
        now = datetime(2026, 7, 22, 12, 0, tzinfo=ZoneInfo("Asia/Tokyo"))

        result = daily_forecasts_for_ha(days, now=now)

        self.assertEqual([item["datetime"] for item in result], [days[1].datetime])


if __name__ == "__main__":
    unittest.main()
