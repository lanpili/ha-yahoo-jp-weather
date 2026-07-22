"""Convert parsed Yahoo data into Home Assistant forecast dictionaries."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from .parser import DailyForecast, HourlyForecast


def _without_none(data: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in data.items() if value is not None}


def hourly_forecasts_for_ha(
    forecasts: list[HourlyForecast], *, now: datetime
) -> list[dict[str, Any]]:
    """Return active and future Yahoo three-hour slots in HA format."""
    cutoff = now - timedelta(hours=3)
    return [
        _without_none(
            {
                "datetime": item.datetime,
                "condition": item.condition,
                "native_temperature": item.temperature,
                "humidity": item.humidity,
                "native_precipitation": item.precipitation,
                "wind_bearing": item.wind_bearing,
                "native_wind_speed": item.wind_speed,
            }
        )
        for item in forecasts
        if datetime.fromisoformat(item.datetime) > cutoff
        and (item.condition is not None or item.temperature is not None)
    ]


def daily_forecasts_for_ha(
    forecasts: list[DailyForecast],
) -> list[dict[str, Any]]:
    """Return Yahoo-derived daily slots in HA format."""
    return [
        _without_none(
            {
                "datetime": item.datetime,
                "condition": item.condition,
                "native_temperature": item.temperature,
                "native_templow": item.temperature_low,
                "native_precipitation": item.precipitation,
                "precipitation_probability": item.precipitation_probability,
            }
        )
        for item in forecasts
    ]
