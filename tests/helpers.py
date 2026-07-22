from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

JST = ZoneInfo("Asia/Tokyo")


def weather_html(*, now: datetime | None = None, area: str = "江戸川区") -> str:
    """Return a small, current, synthetic Yahoo-like weather page."""
    current = (
        (now or datetime.now(JST)).astimezone(JST).replace(second=0, microsecond=0)
    )
    published = current.strftime("%Y年%-m月%-d日　%H時%M分発表")
    heading = current.strftime("今日の天気 - %-m月%-d日")
    hour = current.hour - current.hour % 3
    return f"""
    <html><head><title>{area}の天気 - Yahoo!天気・災害</title></head><body>
      <p id="yjw_pinpoint">{published}</p>
      <div id="yjw_pinpoint_today">
        <h3>{heading}</h3>
        <table><tbody>
          <tr><th>時刻</th><td>{hour}時</td></tr>
          <tr><th>天気</th><td>晴れ</td></tr>
          <tr><th>気温（℃）</th><td>28</td></tr>
          <tr><th>湿度（％）</th><td>60</td></tr>
          <tr><th>降水量（mm）</th><td>0</td></tr>
          <tr><th>風向 風速（m/s）</th><td>南 3</td></tr>
        </tbody></table>
      </div>
    </body></html>
    """
