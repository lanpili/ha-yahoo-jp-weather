"""Constants for Yahoo! Japan Weather."""

from datetime import timedelta

DOMAIN = "yahoo_jp_weather"
CONFIG_VERSION = 2
USER_AGENT = "HomeAssistant YahooJapanWeather"
CONF_ENTITY_UNIQUE_ID = "entity_unique_id"
CONF_NAME = "name"
DEFAULT_NAME = "江戸川区"
DEFAULT_URL = "https://weather.yahoo.co.jp/weather/jp/13/4410/13123.html"
DEFAULT_UPDATE_INTERVAL = timedelta(minutes=30)
PLATFORMS = ["weather"]
