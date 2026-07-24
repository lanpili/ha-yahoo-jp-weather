"""Parse Yahoo! JAPAN Weather App API responses."""

from __future__ import annotations

import json
from datetime import datetime, time, timedelta
from typing import Any

from .parser import (
    JST,
    WIND_BEARINGS,
    DailyForecast,
    HourlyForecast,
    WeatherData,
    map_condition,
)


def _number(value: Any) -> float | None:
    if value is None or value == "" or str(value) == "999":
        return None
    try:
        return float(value)
    except (TypeError, ValueError) as err:
        raise ValueError(f"Yahoo weather value is not numeric: {value!r}") from err


def _probability(value: Any) -> float | None:
    if value is None or value == "":
        return None
    result = _number(value)
    if result is None or not 0 <= result <= 100:
        raise ValueError("Yahoo precipitation probability is outside the valid range")
    return result


def _in_range(name: str, value: float | None, minimum: float, maximum: float) -> None:
    if value is not None and not minimum <= value <= maximum:
        raise ValueError(f"Yahoo weather {name} is outside the valid range")


def _wind_bearing(value: Any) -> float | None:
    if not isinstance(value, str):
        return None
    return WIND_BEARINGS.get(value)


def _object(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"Yahoo App {name} is not an object")
    return value


def _optional_object(container: dict[str, Any], key: str, name: str) -> dict[str, Any]:
    value = container.get(key)
    return {} if value is None else _object(value, name)


def _aware_datetime(value: Any, name: str) -> datetime:
    try:
        result = datetime.fromisoformat(value)
    except (TypeError, ValueError) as err:
        raise ValueError(f"Yahoo App {name} is invalid") from err
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError(f"Yahoo App {name} is missing timezone information")
    return result.astimezone(JST)


def parse_weather_api(payload: str, *, now: datetime | None = None) -> WeatherData:
    """Parse one response from Yahoo's App forecast API."""
    try:
        root = json.loads(payload)
        result = _object(root["ResultSet"]["Result"][0], "result")
        days = result["Day"]
    except (json.JSONDecodeError, KeyError, IndexError, TypeError) as err:
        raise ValueError(
            "Yahoo App forecast response has an unexpected structure"
        ) from err

    if not isinstance(days, list) or not days:
        raise ValueError("Yahoo App forecast did not contain days")

    now_jst = (now or datetime.now(JST)).astimezone(JST)
    try:
        first_day = _object(days[0], "day")
        published = _aware_datetime(first_day["RefTime"], "publication timestamp")
    except (KeyError, TypeError, ValueError) as err:
        raise ValueError(
            f"Yahoo App forecast publication timestamp is invalid: {err}"
        ) from err
    age = now_jst - published
    if age > timedelta(hours=18) or age < timedelta(hours=-1):
        raise ValueError("Yahoo App forecast is stale")

    hourly: list[HourlyForecast] = []
    daily: list[DailyForecast] = []
    for raw_day in days[:10]:
        try:
            day = _object(raw_day, "day")
            date_value = datetime.fromisoformat(day["Date"]).date()
            weather = _object(day["Weather"], "daily weather")
            temp = _object(day.get("Temp", {}), "daily temperature")
        except (KeyError, TypeError, ValueError) as err:
            raise ValueError(f"Yahoo App daily forecast is malformed: {err}") from err

        day_hourly: list[HourlyForecast] = []
        slots = day.get("Hour", []) or []
        if not isinstance(slots, list):
            raise ValueError("Yahoo App hourly forecast is malformed")
        for raw_slot in slots:
            try:
                slot = _object(raw_slot, "hourly forecast")
                slot_weather = _object(slot["Weather"], "hourly weather")
                slot_time = _aware_datetime(slot["Time"], "hourly timestamp")
            except (KeyError, TypeError, ValueError) as err:
                raise ValueError(
                    f"Yahoo App hourly forecast is malformed: {err}"
                ) from err

            precipitation_obj = _optional_object(slot, "Precip", "precipitation")
            wind_speed_obj = _optional_object(slot, "WindSpeed", "wind speed")
            wind_direction_obj = _optional_object(
                slot, "WindDirection", "wind direction"
            )
            temperature = _number(slot.get("Temp"))
            humidity = _number(slot.get("Humidity"))
            precipitation = _number(precipitation_obj.get("0"))
            probability = _probability(slot.get("ProbPrecip"))
            wind_speed = _number(wind_speed_obj.get("0"))
            _in_range("temperature", temperature, -100, 70)
            _in_range("humidity", humidity, 0, 100)
            _in_range("precipitation", precipitation, 0, 500)
            _in_range("wind speed", wind_speed, 0, 150)
            item = HourlyForecast(
                datetime=slot_time.isoformat(),
                condition=map_condition(
                    str(slot_weather.get("Telop", "")), slot_weather.get("Code")
                ),
                temperature=temperature,
                humidity=humidity,
                precipitation=precipitation,
                wind_bearing=_wind_bearing(wind_direction_obj.get("Name")),
                wind_speed=wind_speed,
                precipitation_probability=probability,
            )
            hourly.append(item)
            day_hourly.append(item)

        daily_precipitation = [
            item.precipitation for item in day_hourly if item.precipitation is not None
        ]
        max_temp = _number(temp.get("Max"))
        min_temp = _number(temp.get("Min"))
        _in_range("daily maximum temperature", max_temp, -100, 70)
        _in_range("daily minimum temperature", min_temp, -100, 70)
        daily.append(
            DailyForecast(
                datetime=datetime.combine(date_value, time(0), tzinfo=JST).isoformat(),
                condition=map_condition(
                    str(weather.get("Telop", "")), weather.get("Code")
                ),
                temperature=max_temp,
                temperature_low=min_temp,
                precipitation=round(sum(daily_precipitation), 2)
                if daily_precipitation
                else None,
                precipitation_probability=_probability(day.get("Precip")),
            )
        )

    if not hourly:
        raise ValueError("Yahoo App forecast did not contain hourly data")
    hourly.sort(key=lambda item: item.datetime)
    daily.sort(key=lambda item: item.datetime)
    if not any(
        datetime.fromisoformat(item.datetime) > now_jst - timedelta(hours=1)
        for item in hourly
    ):
        raise ValueError("Yahoo App hourly forecast slots are expired")
    past = [item for item in hourly if datetime.fromisoformat(item.datetime) <= now_jst]
    current = past[-1] if past else hourly[0]

    return WeatherData(
        area_name=str(result.get("JisName") or "Yahoo! Japan"),
        published_at=published.isoformat(),
        current=current,
        hourly=hourly,
        daily=daily,
    )
