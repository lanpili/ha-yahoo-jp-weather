"""Pure parsing helpers for Yahoo! Japan weather pages."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from html.parser import HTMLParser
import re
from zoneinfo import ZoneInfo

JST = ZoneInfo("Asia/Tokyo")

WIND_BEARINGS = {
    "北": 0.0,
    "北北東": 22.5,
    "北東": 45.0,
    "東北東": 67.5,
    "東": 90.0,
    "東南東": 112.5,
    "南東": 135.0,
    "南南東": 157.5,
    "南": 180.0,
    "南南西": 202.5,
    "南西": 225.0,
    "西南西": 247.5,
    "西": 270.0,
    "西北西": 292.5,
    "北西": 315.0,
    "北北西": 337.5,
}


@dataclass(frozen=True, slots=True)
class HourlyForecast:
    """One Yahoo three-hour forecast slot."""

    datetime: str
    condition: str | None
    temperature: float | None
    humidity: float | None
    precipitation: float | None
    wind_bearing: float | None
    wind_speed: float | None


@dataclass(frozen=True, slots=True)
class DailyForecast:
    """Daily values derived from Yahoo three-hour slots."""

    datetime: str
    condition: str | None
    temperature: float | None
    temperature_low: float | None
    precipitation: float | None
    precipitation_probability: float | None = None


@dataclass(frozen=True, slots=True)
class WeatherData:
    """Parsed Yahoo weather data."""

    area_name: str
    published_at: str | None
    current: HourlyForecast
    hourly: list[HourlyForecast]
    daily: list[DailyForecast]


def map_condition(text: str) -> str | None:
    """Map Japanese Yahoo weather wording to a Home Assistant condition."""
    normalized = text.replace(" ", "").replace("　", "")
    if "雷" in normalized:
        return "lightning-rainy" if "雨" in normalized else "lightning"
    if "雪" in normalized:
        return "snowy"
    if "雨" in normalized:
        return "rainy"
    if "晴" in normalized and "曇" in normalized:
        return "partlycloudy"
    if "曇" in normalized:
        return "cloudy"
    if "晴" in normalized:
        return "sunny"
    return None


class _YahooTableParser(HTMLParser):
    """Collect pinpoint and weekly forecast tables."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.active_section: str | None = None
        self.section_depth: int | None = None
        self.sections: dict[str, dict[str, object]] = {}
        self.current_row: list[list[str]] | None = None
        self.current_cell: list[str] | None = None
        self.heading_parts: list[str] | None = None
        self.title_parts: list[str] | None = None
        self.title = ""
        self.page_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.depth += 1
        attrs_dict = dict(attrs)
        if tag == "title":
            self.title_parts = []
        if tag == "div" and attrs_dict.get("id") in {
            "yjw_pinpoint_today",
            "yjw_pinpoint_tomorrow",
            "yjw_week",
        }:
            self.active_section = attrs_dict["id"]
            self.section_depth = self.depth
            self.sections[self.active_section] = {"heading": "", "rows": []}
        if self.active_section:
            if tag == "h3":
                self.heading_parts = []
            elif tag == "tr":
                self.current_row = []
            elif tag == "td" and self.current_row is not None:
                self.current_cell = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.title = "".join(self.title_parts or [])
            self.title_parts = None
        if self.active_section:
            section = self.sections[self.active_section]
            if tag == "td" and self.current_cell is not None:
                assert self.current_row is not None
                self.current_row.append(self.current_cell)
                self.current_cell = None
            elif tag == "tr" and self.current_row is not None:
                rows = section["rows"]
                assert isinstance(rows, list)
                rows.append(self.current_row)
                self.current_row = None
            elif tag == "h3" and self.heading_parts is not None:
                section["heading"] = "".join(self.heading_parts)
                self.heading_parts = None
            if tag == "div" and self.depth == self.section_depth:
                self.active_section = None
                self.section_depth = None
        self.depth -= 1

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if not text:
            return
        self.page_parts.append(text)
        if self.title_parts is not None:
            self.title_parts.append(text)
        if self.heading_parts is not None:
            self.heading_parts.append(text)
        if self.current_cell is not None:
            self.current_cell.append(text)


def _number(parts: list[str] | None) -> float | None:
    if not parts:
        return None
    match = re.search(r"-?\d+(?:\.\d+)?", " ".join(parts))
    return float(match.group()) if match else None


def _numbers(parts: list[str] | None) -> list[float]:
    if not parts:
        return []
    return [float(value) for value in re.findall(r"-?\d+(?:\.\d+)?", " ".join(parts))]


def _row_map(rows: list[list[list[str]]]) -> dict[str, list[list[str]]]:
    result: dict[str, list[list[str]]] = {}
    for row in rows:
        if not row:
            continue
        label = "".join(row[0]).replace(" ", "").replace("　", "")
        result[label] = row[1:]
    return result


def _value(values: list[list[str]], index: int) -> list[str] | None:
    return values[index] if index < len(values) else None


def _forecast_year(published: datetime, month: int) -> int:
    if published.month == 12 and month == 1:
        return published.year + 1
    if published.month == 1 and month == 12:
        return published.year - 1
    return published.year


def parse_weather_html(html: str, *, now: datetime | None = None) -> WeatherData:
    """Parse Yahoo! Japan pinpoint weather HTML."""
    parser = _YahooTableParser()
    parser.feed(html)
    page_text = " ".join(parser.page_parts)

    title_match = re.search(r"([^<>]+?)の天気\s*-\s*Yahoo", parser.title)
    area_name = title_match.group(1).strip() if title_match else "Yahoo! Japan"

    published_match = re.search(
        r"(\d{4})年(\d{1,2})月(\d{1,2})日\s*(\d{1,2})時(\d{2})分発表",
        page_text,
    )
    if published_match:
        published = datetime(
            *(int(value) for value in published_match.groups()), tzinfo=JST
        )
        published_at: str | None = published.isoformat()
    else:
        published = (now or datetime.now(JST)).astimezone(JST)
        published_at = None

    hourly: list[HourlyForecast] = []
    for section in parser.sections.values():
        heading = str(section["heading"])
        date_match = re.search(r"(\d{1,2})月(\d{1,2})日", heading)
        if not date_match:
            continue
        month, day = (int(value) for value in date_match.groups())
        year = _forecast_year(published, month)
        rows_obj = section["rows"]
        assert isinstance(rows_obj, list)
        rows = _row_map(rows_obj)
        times = rows.get("時刻", [])
        conditions = rows.get("天気", [])
        temperatures = rows.get("気温（℃）", [])
        humidities = rows.get("湿度（％）", [])
        precipitation = rows.get("降水量（mm）", [])
        winds = next(
            (values for key, values in rows.items() if "風向" in key and "風速" in key),
            [],
        )
        for index, time_parts in enumerate(times):
            hour_value = _number(time_parts)
            if hour_value is None:
                continue
            slot_time = datetime.combine(
                datetime(year, month, day).date(),
                time(hour=int(hour_value)),
                tzinfo=JST,
            )
            condition_parts = _value(conditions, index) or []
            wind_parts = _value(winds, index) or []
            wind_direction = next(
                (part for part in wind_parts if part in WIND_BEARINGS), None
            )
            hourly.append(
                HourlyForecast(
                    datetime=slot_time.isoformat(),
                    condition=map_condition("".join(condition_parts)),
                    temperature=_number(_value(temperatures, index)),
                    humidity=_number(_value(humidities, index)),
                    precipitation=_number(_value(precipitation, index)),
                    wind_bearing=WIND_BEARINGS.get(wind_direction),
                    wind_speed=_number(
                        [part for part in wind_parts if part != wind_direction]
                    ),
                )
            )

    if not hourly:
        raise ValueError("Yahoo forecast tables were not found")
    hourly.sort(key=lambda item: item.datetime)

    now_jst = (now or datetime.now(JST)).astimezone(JST)
    past = [item for item in hourly if datetime.fromisoformat(item.datetime) <= now_jst]
    current = past[-1] if past else hourly[0]

    grouped: dict[str, list[HourlyForecast]] = {}
    for item in hourly:
        grouped.setdefault(item.datetime[:10], []).append(item)
    daily: list[DailyForecast] = []
    for day, items in grouped.items():
        temperatures_for_day = [
            item.temperature for item in items if item.temperature is not None
        ]
        precipitation_for_day = [
            item.precipitation for item in items if item.precipitation is not None
        ]
        noon = next(
            (
                item
                for item in items
                if datetime.fromisoformat(item.datetime).hour == 12
            ),
            items[0],
        )
        daily.append(
            DailyForecast(
                datetime=datetime.combine(
                    datetime.fromisoformat(day).date(), time(0), tzinfo=JST
                ).isoformat(),
                condition=noon.condition,
                temperature=max(temperatures_for_day) if temperatures_for_day else None,
                temperature_low=min(temperatures_for_day)
                if temperatures_for_day
                else None,
                precipitation=sum(precipitation_for_day)
                if precipitation_for_day
                else None,
            )
        )

    weekly = parser.sections.get("yjw_week")
    if weekly:
        rows_obj = weekly["rows"]
        assert isinstance(rows_obj, list)
        rows = _row_map(rows_obj)
        dates = rows.get("日付", [])
        conditions = rows.get("天気", [])
        temperatures = rows.get("気温（℃）", [])
        probabilities = next(
            (values for key, values in rows.items() if "降水" in key and "確率" in key),
            [],
        )
        existing_days = {item.datetime[:10] for item in daily}
        for index, date_parts in enumerate(dates):
            date_match = re.search(r"(\d{1,2})月(\d{1,2})日", "".join(date_parts))
            if not date_match:
                continue
            month, day = (int(value) for value in date_match.groups())
            year = _forecast_year(published, month)
            date_value = datetime(year, month, day, tzinfo=JST)
            if date_value.date().isoformat() in existing_days:
                continue
            temp_values = _numbers(_value(temperatures, index))
            daily.append(
                DailyForecast(
                    datetime=date_value.isoformat(),
                    condition=map_condition("".join(_value(conditions, index) or [])),
                    temperature=temp_values[0] if temp_values else None,
                    temperature_low=temp_values[1] if len(temp_values) > 1 else None,
                    precipitation=None,
                    precipitation_probability=_number(_value(probabilities, index)),
                )
            )

    daily.sort(key=lambda item: item.datetime)

    return WeatherData(
        area_name=area_name,
        published_at=published_at,
        current=current,
        hourly=hourly,
        daily=daily,
    )
