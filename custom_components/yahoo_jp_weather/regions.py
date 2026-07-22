"""Yahoo! Japan weather region discovery helpers."""

from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
import re
from urllib.parse import urljoin

BASE_URL = "https://weather.yahoo.co.jp"

LOCATION_URL_PATTERN = re.compile(
    r"https://weather\.yahoo\.co\.jp/weather/jp/(\d+)/(\d+)/(\d+)\.html"
)

PREFECTURES: dict[str, str] = {
    "01": "北海道",
    "02": "青森県",
    "03": "岩手県",
    "04": "宮城県",
    "05": "秋田県",
    "06": "山形県",
    "07": "福島県",
    "08": "茨城県",
    "09": "栃木県",
    "10": "群馬県",
    "11": "埼玉県",
    "12": "千葉県",
    "13": "東京都",
    "14": "神奈川県",
    "15": "新潟県",
    "16": "富山県",
    "17": "石川県",
    "18": "福井県",
    "19": "山梨県",
    "20": "長野県",
    "21": "岐阜県",
    "22": "静岡県",
    "23": "愛知県",
    "24": "三重県",
    "25": "滋賀県",
    "26": "京都府",
    "27": "大阪府",
    "28": "兵庫県",
    "29": "奈良県",
    "30": "和歌山県",
    "31": "鳥取県",
    "32": "島根県",
    "33": "岡山県",
    "34": "広島県",
    "35": "山口県",
    "36": "徳島県",
    "37": "香川県",
    "38": "愛媛県",
    "39": "高知県",
    "40": "福岡県",
    "41": "佐賀県",
    "42": "長崎県",
    "43": "熊本県",
    "44": "大分県",
    "45": "宮崎県",
    "46": "鹿児島県",
    "47": "沖縄県",
}


@dataclass(frozen=True, slots=True)
class LocationOption:
    """One selectable Yahoo weather location."""

    code: str
    name: str
    url: str


class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.href: str | None = None
        self.parts: list[str] = []
        self.links: list[tuple[str, list[str]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            self.href = dict(attrs).get("href")
            self.parts = []

    def handle_data(self, data: str) -> None:
        if self.href is None:
            return
        text = " ".join(data.split())
        if text:
            self.parts.append(text)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self.href is not None:
            self.links.append((self.href, self.parts.copy()))
            self.href = None
            self.parts = []


def parse_location_url(url: str) -> tuple[str, str, str] | None:
    """Return prefecture, forecast-area, and municipality codes from a URL."""
    match = LOCATION_URL_PATTERN.fullmatch(url)
    return match.groups() if match else None


def _parse_links(html: str, pattern: re.Pattern[str]) -> list[LocationOption]:
    parser = _LinkParser()
    parser.feed(html)
    result: list[LocationOption] = []
    seen: set[str] = set()
    for href, parts in parser.links:
        url = urljoin(BASE_URL, href)
        match = pattern.fullmatch(url)
        if not match or not parts:
            continue
        code = match.group(1)
        if code in seen:
            continue
        seen.add(code)
        result.append(LocationOption(code=code, name=parts[0], url=url))
    return result


def parse_forecast_areas(html: str, prefecture_code: str) -> list[LocationOption]:
    """Parse forecast-area links from a Yahoo prefecture page."""
    pattern = re.compile(
        rf"https://weather\.yahoo\.co\.jp/weather/jp/{re.escape(prefecture_code)}/(\d+)\.html"
    )
    return _parse_links(html, pattern)


def parse_municipalities(
    html: str, prefecture_code: str, forecast_area_code: str
) -> list[LocationOption]:
    """Parse municipality links from a Yahoo forecast-area page."""
    pattern = re.compile(
        rf"https://weather\.yahoo\.co\.jp/weather/jp/{re.escape(prefecture_code)}/"
        rf"{re.escape(forecast_area_code)}/(\d+)\.html"
    )
    return _parse_links(html, pattern)
