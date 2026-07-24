"""Constants for Yahoo! Japan Weather."""

from datetime import timedelta

DOMAIN = "yahoo_jp_weather"
CONFIG_VERSION = 2
USER_AGENT = "HomeAssistant YahooJapanWeather"
APP_API_URL = "https://weather.yahooapis.jp/Weather/V1/getCityDays"
APP_API_ID = "hgXLJ9Sxg66iaMXpd26qwj.qQ5YnAcQQKfhCdqR4KqQO.qVz.trvfHTCBv0Vwans.Z_.3n.4"
APP_API_USER_AGENT = f"AppVersion:2.8.0; Yahoo AppID: {APP_API_ID}"
CONF_ENTITY_UNIQUE_ID = "entity_unique_id"
CONF_NAME = "name"
DEFAULT_NAME = "江戸川区"
DEFAULT_URL = "https://weather.yahoo.co.jp/weather/jp/13/4410/13123.html"
DEFAULT_UPDATE_INTERVAL = timedelta(minutes=30)
PLATFORMS = ["weather"]
