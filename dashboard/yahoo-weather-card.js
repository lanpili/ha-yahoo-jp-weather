// Yahoo! Japan Weather optional dashboard enhancement v2.2.0
const YAHOO_TRANSLATIONS = {
  zh: {
    locale: "zh-CN", defaultTitle: "Yahoo! JAPAN 天气", close: "关闭",
    forecastType: "天气预报类型", hourly: "每小时", daily: "每日",
    loadingHourly: "正在读取每小时预报…", loadingDaily: "正在读取每日预报…",
    entityRequired: "请设置天气实体", openDetails: "打开天气详情",
    noForecast: "HA 没有返回预报数据", loadFailed: "读取预报失败",
    dragHint: "左右滑动或用鼠标拖动可查看之后的预报", rain: "降雨",
    temperature: "气温", probability: "降水概率", precipitation: "降水量",
    humidity: "湿度", windDirection: "风向", windSpeed: "风速",
    wind: "风向风速", calm: "静风", sunrise: "日出", sunset: "日落",
    unknown: "不明",
    conditions: {
      "clear-night": "晴夜", cloudy: "多云", fog: "雾", hail: "冰雹",
      lightning: "雷电", "lightning-rainy": "雷雨", partlycloudy: "晴间多云",
      pouring: "大雨", rainy: "雨", snowy: "雪", "snowy-rainy": "雨夹雪",
      sunny: "晴", windy: "有风", "windy-variant": "多云有风",
    },
    directions: ["北", "北北东", "东北", "东北东", "东", "东东南", "东南", "南东南", "南", "南西南", "西南", "西西南", "西", "西西北", "西北", "北西北"],
  },
  ja: {
    locale: "ja-JP", defaultTitle: "Yahoo! JAPAN 天気", close: "閉じる",
    forecastType: "天気予報の種類", hourly: "1時間ごと", daily: "毎日",
    loadingHourly: "1時間ごとの予報を読み込んでいます…",
    loadingDaily: "毎日の予報を読み込んでいます…",
    entityRequired: "天気エンティティを設定してください", openDetails: "天気の詳細を開く",
    noForecast: "Home Assistantから予報データが返されませんでした",
    loadFailed: "予報の読み込みに失敗しました",
    dragHint: "左右にスワイプまたはドラッグして今後の予報を表示",
    rain: "降水", temperature: "気温", probability: "降水確率",
    precipitation: "降水量", humidity: "湿度", windDirection: "風向",
    windSpeed: "風速", wind: "風向・風速", calm: "静穏",
    sunrise: "日の出", sunset: "日の入り", unknown: "不明",
    conditions: {
      "clear-night": "晴れ（夜）", cloudy: "曇り", fog: "霧", hail: "ひょう",
      lightning: "雷", "lightning-rainy": "雷雨", partlycloudy: "晴れ時々曇り",
      pouring: "大雨", rainy: "雨", snowy: "雪", "snowy-rainy": "みぞれ",
      sunny: "晴れ", windy: "強風", "windy-variant": "曇り時々強風",
    },
    directions: ["北", "北北東", "北東", "東北東", "東", "東南東", "南東", "南南東", "南", "南南西", "南西", "西南西", "西", "西北西", "北西", "北北西"],
  },
  en: {
    locale: "en-US", defaultTitle: "Yahoo! JAPAN Weather", close: "Close",
    forecastType: "Forecast type", hourly: "Hourly", daily: "Daily",
    loadingHourly: "Loading hourly forecast…", loadingDaily: "Loading daily forecast…",
    entityRequired: "Set a weather entity", openDetails: "Open weather details",
    noForecast: "Home Assistant returned no forecast data",
    loadFailed: "Failed to load forecast",
    dragHint: "Swipe or drag horizontally to view later forecasts", rain: "Rain",
    temperature: "Temp", probability: "Rain %", precipitation: "Rain",
    humidity: "Humidity", windDirection: "Wind", windSpeed: "Speed",
    wind: "Wind direction and speed", calm: "Calm",
    sunrise: "Sunrise", sunset: "Sunset", unknown: "unknown",
    conditions: {
      "clear-night": "Clear night", cloudy: "Cloudy", fog: "Fog", hail: "Hail",
      lightning: "Lightning", "lightning-rainy": "Thunderstorms",
      partlycloudy: "Partly cloudy", pouring: "Pouring rain", rainy: "Rainy",
      snowy: "Snowy", "snowy-rainy": "Sleet", sunny: "Sunny", windy: "Windy",
      "windy-variant": "Cloudy and windy",
    },
    directions: ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"],
  },
};

function yahooTranslation(hass) {
  const language = String(
    hass?.language || hass?.locale?.language || document.documentElement.lang || "zh"
  ).toLowerCase();
  return YAHOO_TRANSLATIONS[language.startsWith("ja") ? "ja" : language.startsWith("en") ? "en" : "zh"];
}

function currentYahooTranslation() {
  return yahooTranslation(document.querySelector("home-assistant")?.hass);
}

class YahooWeatherDialog extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._active = "hourly";
    this._cache = new Map();
    this._requestId = 0;
    this._onKeyDown = (event) => {
      if (event.key === "Escape") this.close();
    };
  }

  setData(hass, config) {
    this._hass = hass;
    this._config = config;
    this._render();
  }

  connectedCallback() {
    window.addEventListener("keydown", this._onKeyDown);
  }

  disconnectedCallback() {
    window.removeEventListener("keydown", this._onKeyDown);
  }

  close() {
    this.remove();
  }

  _render() {
    if (!this._hass || !this._config) return;
    const text = yahooTranslation(this._hass);
    const state = this._hass.states[this._config.entity];
    const title = state?.attributes?.friendly_name || text.defaultTitle;
    this.shadowRoot.innerHTML = `
      <style>
        :host { position: fixed; inset: 0; z-index: 99999; font-family: var(--paper-font-body1_-_font-family, sans-serif); }
        .backdrop { position: absolute; inset: 0; background: rgba(0,0,0,.58); display: flex; align-items: center; justify-content: center; padding: 16px; box-sizing: border-box; }
        .dialog { width: min(820px, calc(100vw - 32px)); max-height: min(86vh, 840px); overflow: hidden; border-radius: 22px; background: var(--card-background-color, #fff); color: var(--primary-text-color, #212121); box-shadow: 0 24px 70px rgba(0,0,0,.45); display: flex; flex-direction: column; }
        .header { display: flex; align-items: center; gap: 12px; padding: 17px 16px 7px 22px; }
        .title { min-width: 0; flex: 1; font-size: 20px; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .close { border: 0; background: transparent; color: var(--secondary-text-color, #666); font-size: 30px; line-height: 36px; width: 40px; height: 40px; border-radius: 50%; cursor: pointer; }
        .close:hover { background: var(--secondary-background-color, rgba(127,127,127,.12)); }
        .tabs { display: grid; grid-template-columns: 1fr 1fr; padding: 0 18px; border-bottom: 1px solid var(--divider-color, rgba(127,127,127,.2)); }
        .tab { position: relative; z-index: 2; min-height: 50px; border: 0; background: transparent; color: var(--secondary-text-color, #666); padding: 13px 8px 14px; font-size: 15px; font-weight: 600; cursor: pointer; touch-action: manipulation; }
        .tab.active { color: var(--primary-color, #03a9f4); }
        .tab.active::after { content: ""; position: absolute; left: 20%; right: 20%; bottom: -1px; height: 3px; border-radius: 3px 3px 0 0; background: var(--primary-color, #03a9f4); }
        .content { min-height: 250px; overflow: hidden; padding: 18px 14px 16px; }
        .loading, .error { min-height: 220px; display: grid; place-items: center; color: var(--secondary-text-color, #666); text-align: center; padding: 20px; }
        .error { color: var(--error-color, #db4437); }
        .hint { color: var(--secondary-text-color, #777); font-size: 12px; padding: 0 8px 10px; }
        .rail { display: flex; gap: 10px; overflow-x: auto; overflow-y: hidden; padding: 2px 6px 14px; scroll-snap-type: x proximity; overscroll-behavior-x: contain; touch-action: pan-x; cursor: grab; scrollbar-width: thin; user-select: none; }
        .rail.dragging { cursor: grabbing; scroll-snap-type: none; }
        .forecast { flex: 0 0 126px; scroll-snap-align: start; box-sizing: border-box; border-radius: 16px; padding: 13px 9px 12px; background: var(--secondary-background-color, rgba(127,127,127,.10)); text-align: center; }
        .forecast.daily { flex-basis: 142px; }
        .when { min-height: 34px; font-size: 13px; color: var(--secondary-text-color, #666); line-height: 1.35; }
        ha-weather-icon { display: inline-block; width: 48px; height: 48px; margin: 6px 0 4px; }
        .condition { min-height: 21px; font-size: 14px; font-weight: 600; }
        .temp { margin-top: 7px; font-size: 19px; font-weight: 650; white-space: nowrap; }
        .low { color: var(--secondary-text-color, #777); font-size: 14px; font-weight: 500; }
        .probability { margin-top: 9px; color: #2789d8; font-size: 14px; font-weight: 700; white-space: nowrap; }
        .rain { margin-top: 4px; color: var(--secondary-text-color, #777); font-size: 12px; white-space: nowrap; }
        @media (max-width: 600px) {
          .backdrop { padding: 10px; }
          .dialog { width: calc(100vw - 20px); max-height: 84vh; border-radius: 18px; }
          .header { padding: 13px 12px 5px 17px; }
          .title { font-size: 18px; }
          .tabs { padding: 0 10px; }
          .content { padding: 14px 8px 12px; min-height: 235px; }
          .forecast { flex-basis: 116px; }
          .forecast.daily { flex-basis: 130px; }
        }
      </style>
      <div class="backdrop" role="presentation">
        <section class="dialog" role="dialog" aria-modal="true">
          <header class="header">
            <div class="title"></div>
            <button class="close" aria-label="${text.close}">×</button>
          </header>
          <nav class="tabs" aria-label="${text.forecastType}">
            <button class="tab active" data-type="hourly">${text.hourly}</button>
            <button class="tab" data-type="daily">${text.daily}</button>
          </nav>
          <main class="content"><div class="loading">${text.loadingHourly}</div></main>
        </section>
      </div>`;
    this.shadowRoot.querySelector(".title").textContent = title;
    this.shadowRoot.querySelector(".close").addEventListener("click", () => this.close());
    this.shadowRoot.querySelector(".backdrop").addEventListener("click", (event) => {
      if (event.target.classList.contains("backdrop")) this.close();
    });
    for (const button of this.shadowRoot.querySelectorAll(".tab")) {
      button.addEventListener("click", () => this._select(button.dataset.type));
    }
    this._loadForecast("hourly");
  }

  _select(type) {
    this._active = type;
    for (const button of this.shadowRoot.querySelectorAll(".tab")) {
      button.classList.toggle("active", button.dataset.type === type);
    }
    if (this._cache.has(type)) {
      this._showForecast(this._cache.get(type), type);
    } else {
      this._loadForecast(type);
    }
  }

  async _loadForecast(type) {
    const requestId = ++this._requestId;
    const text = yahooTranslation(this._hass);
    const content = this.shadowRoot.querySelector(".content");
    content.innerHTML = `<div class="loading">${type === "hourly" ? text.loadingHourly : text.loadingDaily}</div>`;
    try {
      const response = await this._hass.callWS({
        type: "call_service",
        domain: "weather",
        service: "get_forecasts",
        service_data: { type },
        target: { entity_id: this._config.entity },
        return_response: true,
      });
      const forecasts = this._findForecast(response);
      if (!forecasts?.length) throw new Error(text.noForecast);
      this._cache.set(type, forecasts);
      if (requestId === this._requestId && this._active === type) {
        this._showForecast(forecasts, type);
      }
    } catch (error) {
      if (requestId === this._requestId) {
        content.innerHTML = `<div class="error"></div>`;
        content.querySelector(".error").textContent = `${text.loadFailed}: ${error?.message || error}`;
      }
    }
  }

  _findForecast(value, seen = new Set()) {
    if (!value || typeof value !== "object" || seen.has(value)) return null;
    seen.add(value);
    if (Array.isArray(value.forecast)) return value.forecast;
    for (const child of Object.values(value)) {
      const found = this._findForecast(child, seen);
      if (found) return found;
    }
    return null;
  }

  _showForecast(forecasts, type) {
    const text = yahooTranslation(this._hass);
    const content = this.shadowRoot.querySelector(".content");
    content.replaceChildren();
    const hint = document.createElement("div");
    hint.className = "hint";
    hint.textContent = text.dragHint;
    const rail = document.createElement("div");
    rail.className = "rail";
    for (const item of forecasts) rail.append(this._forecastElement(item, type));
    content.append(hint, rail);
    this._enableDrag(rail);
  }

  _forecastElement(item, type) {
    const text = yahooTranslation(this._hass);
    const element = document.createElement("article");
    element.className = `forecast ${type === "daily" ? "daily" : "hourly"}`;
    const date = new Date(item.datetime);
    const when = type === "daily"
      ? new Intl.DateTimeFormat(text.locale, { month: "numeric", day: "numeric", weekday: "short", timeZone: "Asia/Tokyo" }).format(date)
      : new Intl.DateTimeFormat(text.locale, { month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit", hour12: false, timeZone: "Asia/Tokyo" }).format(date);
    const condition = item.condition || "cloudy";
    const name = text.conditions[condition] || condition;
    const temperature = item.temperature ?? item.native_temperature;
    const low = item.templow ?? item.native_templow;
    const probability = item.precipitation_probability;
    const precipitation = item.precipitation ?? item.native_precipitation;

    const whenElement = document.createElement("div");
    whenElement.className = "when";
    whenElement.textContent = when;
    const iconElement = document.createElement("ha-weather-icon");
    iconElement.setAttribute("state", condition);
    iconElement.state = condition;
    const conditionElement = document.createElement("div");
    conditionElement.className = "condition";
    conditionElement.textContent = name;
    const tempElement = document.createElement("div");
    tempElement.className = "temp";
    tempElement.textContent = temperature == null ? "--" : `${Math.round(temperature)}°`;
    if (type === "daily" && low != null) {
      const lowElement = document.createElement("span");
      lowElement.className = "low";
      lowElement.textContent = ` / ${Math.round(low)}°`;
      tempElement.append(lowElement);
    }
    const probabilityElement = document.createElement("div");
    probabilityElement.className = "probability";
    probabilityElement.textContent = probability == null
      ? `${text.rain} --`
      : `${text.rain} ${Math.round(probability)}%`;
    const rainElement = document.createElement("div");
    rainElement.className = "rain";
    rainElement.textContent = precipitation == null ? "" : `${Number(precipitation).toFixed(1)} mm`;
    element.append(whenElement, iconElement, conditionElement, tempElement, probabilityElement, rainElement);
    return element;
  }

  _enableDrag(rail) {
    let startX = 0;
    let startScroll = 0;
    rail.addEventListener("pointerdown", (event) => {
      startX = event.clientX;
      startScroll = rail.scrollLeft;
      rail.classList.add("dragging");
      rail.setPointerCapture(event.pointerId);
    });
    rail.addEventListener("pointermove", (event) => {
      if (!rail.classList.contains("dragging")) return;
      rail.scrollLeft = startScroll - (event.clientX - startX);
    });
    const stop = () => rail.classList.remove("dragging");
    rail.addEventListener("pointerup", stop);
    rail.addEventListener("pointercancel", stop);
  }
}

class YahooWeatherCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
  }

  static getStubConfig() {
    return { entity: "weather.home" };
  }

  setConfig(config) {
    if (!config.entity) throw new Error(yahooTranslation(this._hass).entityRequired);
    this._config = { ...config };
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    if (this._card) this._card.hass = hass;
    this.shadowRoot.querySelector(".wrapper")?.setAttribute(
      "aria-label", yahooTranslation(hass).openDetails
    );
  }

  getCardSize() {
    return 4;
  }

  getGridOptions() {
    return this._config?.grid_options || { columns: 12, rows: 4 };
  }

  _render() {
    if (!this._config) return;
    this.shadowRoot.innerHTML = `
      <style>
        :host { display: block; height: 100%; min-height: 100%; cursor: pointer; }
        .wrapper { position: relative; height: 100%; min-height: 100%; box-sizing: border-box; }
        .wrapper > * { display: block; height: 100%; pointer-events: none; }
        .wrapper::after { content: ""; position: absolute; inset: 0; z-index: 20; cursor: pointer; touch-action: manipulation; }
      </style>
      <div class="wrapper" role="button" tabindex="0" aria-label="${yahooTranslation(this._hass).openDetails}"></div>`;
    const wrapper = this.shadowRoot.querySelector(".wrapper");
    const card = document.createElement("hui-weather-forecast-card");
    const nativeConfig = { ...this._config, type: "weather-forecast" };
    delete nativeConfig.grid_options;
    card.setConfig(nativeConfig);
    if (this._hass) card.hass = this._hass;
    wrapper.append(card);
    this._card = card;
    wrapper.addEventListener("click", () => this._open());
    wrapper.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        this._open();
      }
    });
  }

  _open() {
    if (!this._hass) return;
    document.querySelector("yahoo-weather-dialog")?.remove();
    const dialog = document.createElement("yahoo-weather-dialog");
    document.body.append(dialog);
    dialog.setData(this._hass, this._config);
  }
}

if (!customElements.get("yahoo-weather-dialog")) {
  customElements.define("yahoo-weather-dialog", YahooWeatherDialog);
}
if (!customElements.get("yahoo-weather-card")) {
  customElements.define("yahoo-weather-card", YahooWeatherCard);
}

// Home Assistant's native weather more-info dialog renders these tabs inside
// nested shadow roots. Keep the native dialog consistent with this card.
function collectYahooWeatherRoots() {
  const roots = [document];
  for (let index = 0; index < roots.length; index += 1) {
    for (const element of roots[index].querySelectorAll("*")) {
      if (element.shadowRoot) roots.push(element.shadowRoot);
    }
  }
  return roots;
}

function isYahooWeatherDialog(dialog) {
  return String(dialog?.stateObj?.attributes?.attribution || "").includes("Yahoo");
}

function yahooTabKind(tab) {
  const label = tab?.textContent?.trim();
  const hourly = ["每小时", "Hourly", "1時間ごと", "毎時", "時間ごと"];
  const daily = ["每日", "Daily", "毎日", "日ごと", "日別"];
  return hourly.includes(label) ? "hourly" : daily.includes(label) ? "daily" : null;
}

function cleanupNativeWeatherDialog(dialog) {
  dialog.classList.remove("yahoo-hourly-mode");
  dialog.__yahooDefaultHourlyApplied = false;
  const root = dialog.shadowRoot;
  if (!root) return;
  root.querySelector("#yahoo-hourly-adaptive-style")?.remove();
  for (const element of root.querySelectorAll(
    ".yahoo-hourly-details, .yahoo-sun-event, .yahoo-hourly-labels"
  )) element.remove();
  const tabs = [...root.querySelectorAll('ha-tab-group-tab, [role="tab"]')];
  const daily = tabs.find((tab) => yahooTabKind(tab) === "daily");
  const hourly = tabs.find((tab) => yahooTabKind(tab) === "hourly");
  if (daily && hourly && daily.parentElement === hourly.parentElement) {
    daily.parentElement.insertBefore(daily, hourly);
    for (const property of ["position", "z-index"]) {
      daily.parentElement.style.removeProperty(property);
    }
    for (const tab of [daily, hourly]) {
      for (const property of ["position", "z-index", "min-height", "touch-action"]) {
        tab.style.removeProperty(property);
      }
    }
  }
}

function reorderNativeWeatherTabs(roots = collectYahooWeatherRoots()) {
  for (const root of roots) {
    const tabs = [...root.querySelectorAll(
      '[role="tab"], ha-tab-button, ha-tab, mwc-tab'
    )];
    const daily = tabs.find((tab) => yahooTabKind(tab) === "daily");
    const hourly = tabs.find((tab) => yahooTabKind(tab) === "hourly");
    if (!daily || !hourly || daily.parentElement !== hourly.parentElement) continue;

    let node = daily;
    let weatherDialog = null;
    while (node) {
      const host = node.getRootNode?.().host;
      if (!host) break;
      if (host.localName.includes("more-info-weather")) weatherDialog = host;
      node = host;
    }
    if (!weatherDialog || !isYahooWeatherDialog(weatherDialog)) continue;

    const dailyBeforeHourly = Boolean(
      daily.compareDocumentPosition(hourly) & Node.DOCUMENT_POSITION_FOLLOWING
    );
    if (dailyBeforeHourly) daily.parentElement.insertBefore(hourly, daily);

    const tabGroup = daily.parentElement;
    tabGroup.style.position = "relative";
    tabGroup.style.zIndex = "5";
    for (const tab of [hourly, daily]) {
      tab.style.position = "relative";
      tab.style.zIndex = "6";
      tab.style.minHeight = "50px";
      tab.style.touchAction = "manipulation";
    }

    if (!weatherDialog.__yahooDefaultHourlyApplied) {
      weatherDialog.__yahooDefaultHourlyApplied = true;
      window.setTimeout(() => hourly.click(), 0);
    }

    const dialogRoot = daily.getRootNode();
    if (!dialogRoot.__yahooWeatherTabClickProxy) {
      dialogRoot.__yahooWeatherTabClickProxy = true;
      dialogRoot.addEventListener("click", (event) => {
        if (!event.isTrusted || !isYahooWeatherDialog(weatherDialog)) return;
        const currentTabs = [...dialogRoot.querySelectorAll(
          'ha-tab-group-tab, [role="tab"]'
        )].filter((tab) => yahooTabKind(tab));
        if (currentTabs.length !== 2) return;
        const currentGroup = currentTabs[0].parentElement;
        const groupRect = currentGroup.getBoundingClientRect();
        const hitBottom = Math.max(groupRect.bottom, groupRect.top + 54);
        if (
          event.clientY < groupRect.top ||
          event.clientY > hitBottom ||
          event.clientX < groupRect.left ||
          event.clientX > groupRect.right
        ) return;
        const targetTab = currentTabs.find((tab) => {
          const rect = tab.getBoundingClientRect();
          return event.clientX >= rect.left && event.clientX <= rect.right;
        });
        if (!targetTab) return;
        event.preventDefault();
        event.stopImmediatePropagation();
        targetTab.click();
      }, true);
    }
  }
}

function addNativeWeatherProbabilities(roots = collectYahooWeatherRoots()) {
  const weatherDialogs = [];
  for (const root of roots) {
    for (const element of root.querySelectorAll("*")) {
      if (element.localName?.includes("more-info-weather")) {
        if (isYahooWeatherDialog(element)) weatherDialogs.push(element);
        else cleanupNativeWeatherDialog(element);
      }
    }
  }

  for (const dialog of weatherDialogs) {
    const text = currentYahooTranslation();
    const forecast = dialog._forecastEvent?.forecast;
    const forecastType = dialog._forecastEvent?.type;
    dialog.classList.toggle("yahoo-hourly-mode", forecastType === "hourly");
    const items = dialog.shadowRoot?.querySelectorAll(
      ".forecast-item:not(.yahoo-sun-event)"
    );
    if (!Array.isArray(forecast) || !items?.length) continue;

    const hass = document.querySelector("home-assistant")?.hass;
    const sun = hass?.states?.["sun.sun"]?.attributes;
    const sunEvents = [
      [text.sunrise, sun?.next_rising],
      [text.sunset, sun?.next_setting],
    ].filter((event) => event[1]);
    const windDirections = text.directions;

    if (!dialog.shadowRoot.querySelector("#yahoo-hourly-adaptive-style")) {
      const style = document.createElement("style");
      style.id = "yahoo-hourly-adaptive-style";
      style.textContent = `
        :host(.yahoo-hourly-mode) .forecast {
          justify-content: flex-start !important;
          mask-image: none !important;
          padding-left: 0 !important;
          padding-right: 0 !important;
        }
        :host(.yahoo-hourly-mode) .forecast-item {
          box-sizing: border-box;
          flex: 0 0 48px;
          width: 48px;
          min-width: 48px;
          padding: 0 2px !important;
        }
        :host(.yahoo-hourly-mode) .forecast-item-label { font-size: 12px !important; }
        :host(.yahoo-hourly-mode) .forecast-image-icon { padding: 2px 0 !important; }
        :host(.yahoo-hourly-mode) .forecast-image-icon > * {
          width: 32px !important; height: 32px !important;
          --mdc-icon-size: 32px !important;
        }
        :host(.yahoo-hourly-mode) .forecast .temp {
          margin: 2px 0 !important;
          font-size: 16px !important;
          line-height: 22px;
        }
        :host(.yahoo-hourly-mode) .forecast .templow { display: none !important; }
        .yahoo-sun-event .yahoo-sun-name {
          font-size: 10.5px !important; line-height: 22px !important;
          color: var(--secondary-text-color);
        }
        .yahoo-sun-event .forecast-image-icon ha-icon {
          color: #f6a623; --mdc-icon-size: 28px !important;
        }
        .yahoo-hourly-details {
          display: flex; flex-direction: column; align-items: center;
          gap: 0; margin-top: 0;
        }
        .yahoo-hourly-details > * {
          margin: 0 !important; font-size: 10.5px !important;
          line-height: 18px !important; white-space: nowrap;
        }
        .yahoo-hourly-wind {
          display: flex !important; flex-direction: column;
          align-items: center; justify-content: center; gap: 0;
          line-height: 16px !important;
        }
        .yahoo-wind-arrow {
          width: 8px; height: 12px; color: var(--primary-color);
          flex: 0 0 12px; transform-origin: 50% 50%;
        }
        .yahoo-wind-calm {
          display: inline-block; width: 10px; height: 2px;
          margin: 5px 0; border-radius: 1px; background: #979797;
          flex: 0 0 2px;
        }
        .yahoo-wind-direction, .yahoo-wind-speed {
          display: block; line-height: 16px;
        }
        .yahoo-expanded-label { display: none !important; }
        .yahoo-hourly-labels {
          position: sticky; left: 0; align-self: stretch;
          flex: 0 0 58px; width: 58px; min-width: 58px;
          z-index: 8; pointer-events: none;
          background: var(--card-background-color, var(--ha-card-background));
          box-shadow: 4px 0 6px -6px rgba(0,0,0,.45);
        }
        .yahoo-hourly-label {
          position: absolute; left: 0; right: 0;
          display: flex; align-items: center; justify-content: flex-end;
          box-sizing: border-box; padding-right: 6px;
          color: var(--secondary-text-color);
          font-size: 10px; line-height: 1.1; white-space: nowrap;
        }
        .yahoo-hourly-labels + .forecast-day { margin-left: 6px; }
        @media (max-height: 599px) {
          :host(.yahoo-hourly-mode) .forecast-item { flex-basis: 46px; width: 46px; min-width: 46px; }
          .yahoo-hourly-labels { flex-basis: 54px; width: 54px; min-width: 54px; }
          .yahoo-hourly-details > * { font-size: 10px !important; line-height: 16px !important; }
        }
        @media (min-height: 801px) {
          .yahoo-hourly-details > * { line-height: 19px !important; }
        }
      `;
      dialog.shadowRoot.append(style);
    }

    const upsertDetail = (item, className, text, title) => {
      let element = item.querySelector(`:scope > .${className}`);
      if (!text) {
        element?.remove();
        return;
      }
      if (!element) {
        element = document.createElement("div");
        element.className = className;
        element.style.cssText = [
          "color:var(--secondary-text-color)",
          "font-size:var(--ha-font-size-xs,11px)",
          "line-height:1.45",
          "white-space:nowrap",
        ].join(";");
        item.append(element);
      }
      element.textContent = text;
      element.title = title || text;
    };
    const formatCompact = (value) => {
      const number = Number(value);
      return Number.isInteger(number) ? String(number) : number.toFixed(1);
    };

    items.forEach((item, index) => {
      const forecastItem = forecast[index] || {};
      const probability = forecastItem.precipitation_probability;
      let details = item.querySelector(":scope > .yahoo-hourly-details");
      if (!details) {
        details = document.createElement("div");
        details.className = "yahoo-hourly-details";
        item.append(details);
      }
      let probabilityElement = details.querySelector(
        ":scope > .yahoo-precipitation-probability"
      );
      if (probability == null) {
        probabilityElement?.remove();
      } else {
        if (!probabilityElement) {
          probabilityElement = document.createElement("div");
          probabilityElement.className = "yahoo-precipitation-probability";
          probabilityElement.style.cssText = [
            "color:var(--primary-color)",
            "font-size:var(--ha-font-size-s,12px)",
            "font-weight:var(--ha-font-weight-medium,500)",
            "line-height:1.4",
            "margin-top:var(--ha-space-1,4px)",
            "white-space:nowrap",
          ].join(";");
          details.append(probabilityElement);
        }
        probabilityElement.replaceChildren();
        const probabilityLabel = document.createElement("span");
        probabilityLabel.className = "yahoo-expanded-label";
        probabilityLabel.textContent = `${text.probability} `;
        probabilityElement.append(
          probabilityLabel,
          document.createTextNode(`${Math.round(probability)}%`)
        );
        probabilityElement.title = `${text.probability} ${Math.round(probability)}%`;
      }

      if (forecastType !== "hourly") {
        upsertDetail(details, "yahoo-hourly-precipitation", "");
        upsertDetail(details, "yahoo-hourly-humidity", "");
        upsertDetail(details, "yahoo-hourly-wind", "");
        upsertDetail(details, "yahoo-hourly-sun", "");
        return;
      }

      const precipitation = forecastItem.precipitation;
      upsertDetail(
        details,
        "yahoo-hourly-precipitation",
        precipitation == null
          ? ""
          : `${formatCompact(precipitation)}mm`,
        precipitation == null
          ? ""
          : `${text.precipitation} ${formatCompact(precipitation)}mm`
      );
      const precipitationElement = details.querySelector(
        ":scope > .yahoo-hourly-precipitation"
      );
      if (precipitationElement && precipitation != null) {
        precipitationElement.replaceChildren();
        const label = document.createElement("span");
        label.className = "yahoo-expanded-label";
        label.textContent = `${text.precipitation} `;
        precipitationElement.append(
          label,
          document.createTextNode(`${formatCompact(precipitation)}mm`)
        );
      }

      const humidity = forecastItem.humidity;
      upsertDetail(
        details,
        "yahoo-hourly-humidity",
        humidity == null ? "" : `${Math.round(humidity)}%`,
        humidity == null ? "" : `${text.humidity} ${Math.round(humidity)}%`
      );

      const windSpeed = forecastItem.wind_speed;
      const windBearing = Number(forecastItem.wind_bearing);
      let windText = "";
      let windSpeedMeters = null;
      let speedText = "";
      if (windSpeed != null) {
        const windSpeedUnit = dialog.stateObj?.attributes?.wind_speed_unit;
        windSpeedMeters = windSpeedUnit === "km/h"
          ? Number(windSpeed) / 3.6
          : Number(windSpeed);
        speedText = `${formatCompact(windSpeedMeters)}m`;
        if (windSpeedMeters === 0) {
          windText = `${text.calm} ${speedText}`;
        } else if (Number.isFinite(windBearing)) {
          const direction = windDirections[
            Math.round(((windBearing % 360) + 360) % 360 / 22.5) % 16
          ];
          windText = `${direction} ${speedText}`;
        } else {
          windText = speedText;
        }
      }
      upsertDetail(details, "yahoo-hourly-wind", windText, `${text.wind} ${windText}`);
      const windElement = details.querySelector(":scope > .yahoo-hourly-wind");
      if (windElement && windSpeedMeters != null) {
        windElement.replaceChildren();
        if (windSpeedMeters === 0) {
          const calm = document.createElement("span");
          calm.className = "yahoo-wind-calm";
          windElement.append(calm);
        } else if (Number.isFinite(windBearing)) {
          const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
          svg.setAttribute("viewBox", "0 0 24 36");
          svg.setAttribute("aria-hidden", "true");
          svg.classList.add("yahoo-wind-arrow");
          svg.style.transform = `rotate(${windBearing}deg)`;
          const arrow = document.createElementNS("http://www.w3.org/2000/svg", "path");
          arrow.setAttribute("d", "M12 0 L24 36 L12 27 L0 36 Z");
          arrow.setAttribute("fill", "currentColor");
          svg.append(arrow);
          windElement.append(svg);
        }
        const directionText = document.createElement("span");
        directionText.className = "yahoo-wind-direction";
        directionText.textContent = Number.isFinite(windBearing) && windSpeedMeters !== 0
          ? windDirections[
            Math.round(((windBearing % 360) + 360) % 360 / 22.5) % 16
          ]
          : windSpeedMeters === 0 ? text.calm : "—";
        const speedValue = document.createElement("span");
        speedValue.className = "yahoo-wind-speed";
        speedValue.textContent = speedText;
        windElement.append(directionText, speedValue);
      }

      upsertDetail(details, "yahoo-hourly-sun", "");
    });

    const activeSunEvents = new Set();
    if (forecastType === "hourly") {
      for (const [label, eventValue] of sunEvents) {
        const eventTime = Date.parse(eventValue);
        const slotIndex = forecast.findIndex((forecastItem, index) => {
          const start = Date.parse(forecastItem.datetime);
          const end = index + 1 < forecast.length
            ? Date.parse(forecast[index + 1].datetime)
            : start + 60 * 60 * 1000;
          return eventTime >= start && eventTime < end;
        });
        if (slotIndex < 0 || !items[slotIndex]) continue;
        const eventKey = `${label}-${eventValue}`;
        activeSunEvents.add(eventKey);
        let eventColumn = [...dialog.shadowRoot.querySelectorAll(".yahoo-sun-event")]
          .find((column) => column.dataset.eventKey === eventKey);
        if (!eventColumn) {
          eventColumn = document.createElement("div");
          eventColumn.className = "forecast-item yahoo-sun-event";
          eventColumn.dataset.eventKey = eventKey;

          const timeLabel = document.createElement("div");
          timeLabel.className = "forecast-item-label";
          timeLabel.textContent = new Intl.DateTimeFormat(text.locale, {
            hour: "2-digit",
            minute: "2-digit",
            hour12: false,
            timeZone: "Asia/Tokyo",
          }).format(new Date(eventValue));

          const iconWrapper = document.createElement("div");
          iconWrapper.className = "forecast-image-icon";
          const icon = document.createElement("ha-icon");
          icon.setAttribute(
            "icon",
            label === text.sunrise ? "mdi:weather-sunset-up" : "mdi:weather-sunset-down"
          );
          iconWrapper.append(icon);

          const eventName = document.createElement("div");
          eventName.className = "temp yahoo-sun-name";
          eventName.textContent = label;
          const templow = document.createElement("div");
          templow.className = "templow";
          eventColumn.append(timeLabel, iconWrapper, eventName, templow);
        }
        items[slotIndex].after(eventColumn);
      }
    }
    for (const eventColumn of dialog.shadowRoot.querySelectorAll(".yahoo-sun-event")) {
      if (!activeSunEvents.has(eventColumn.dataset.eventKey)) eventColumn.remove();
    }

    const forecastScroller = dialog.shadowRoot.querySelector(".forecast");
    let labelColumn = forecastScroller?.querySelector(":scope > .yahoo-hourly-labels");
    if (forecastType !== "hourly") {
      labelColumn?.remove();
      continue;
    }
    if (!forecastScroller) continue;
    if (!labelColumn) {
      labelColumn = document.createElement("div");
      labelColumn.className = "yahoo-hourly-labels";
      forecastScroller.prepend(labelColumn);
    }

    const sample = items[0];
    const labelColumnRect = labelColumn.getBoundingClientRect();
    const valueRows = [
      [text.temperature, sample.querySelector(".temp")],
      [text.probability, sample.querySelector(".yahoo-precipitation-probability")],
      [text.precipitation, sample.querySelector(".yahoo-hourly-precipitation")],
      [text.humidity, sample.querySelector(".yahoo-hourly-humidity")],
      [text.windDirection, sample.querySelector(".yahoo-hourly-wind")],
      [text.windSpeed, sample.querySelector(".yahoo-wind-speed")],
    ];
    const positionedRows = valueRows
      .filter((row) => row[1])
      .map(([label, target]) => {
        const rect = target.getBoundingClientRect();
        let top = rect.top - labelColumnRect.top;
        let height = rect.height;
        if (label === text.windDirection) {
          const speed = target.querySelector(".yahoo-wind-speed");
          const speedRect = speed?.getBoundingClientRect();
          if (speedRect) height = Math.max(0, speedRect.top - rect.top);
        }
        return [label, Math.round(top), Math.max(14, Math.round(height))];
      });
    const layoutKey = JSON.stringify(positionedRows);
    if (labelColumn.dataset.layout !== layoutKey) {
      labelColumn.dataset.layout = layoutKey;
      labelColumn.replaceChildren();
      for (const [label, top, height] of positionedRows) {
        const row = document.createElement("div");
        row.className = "yahoo-hourly-label";
        row.textContent = label;
        row.style.top = `${top}px`;
        row.style.height = `${height}px`;
        labelColumn.append(row);
      }
    }
    const labelsBottom = positionedRows.reduce(
      (bottom, row) => Math.max(bottom, row[1] + row[2]),
      0
    );
    labelColumn.style.height = `${labelsBottom + 6}px`;
  }
}

function enhanceDashboardWeatherCards(roots = collectYahooWeatherRoots()) {
  const cards = [];
  for (const root of roots) {
    for (const card of root.querySelectorAll("hui-weather-forecast-card")) {
      cards.push(card);
    }
  }

  const text = currentYahooTranslation();
  const directions = text.directions;
  const compactNumber = (value) => {
    const number = Number(value);
    return Number.isInteger(number) ? String(number) : number.toFixed(1);
  };

  for (const card of cards) {
    const config = card._config;
    const entityId = config?.entity;
    const state = card.hass?.states?.[entityId];
    if (
      !entityId ||
      !state ||
      !String(state.attributes?.attribution || "").includes("Yahoo") ||
      config.forecast_type !== "hourly"
    ) continue;

    if (!card.__yahooFullCardTapInstalled) {
      card.__yahooFullCardTapInstalled = true;
      let tap = null;
      card.addEventListener("pointerdown", (event) => {
        const path = event.composedPath();
        const inEditor = path.some((node) =>
          node?.localName?.includes("card-preview") ||
          node?.localName?.includes("dialog-edit-card")
        );
        const inForecast = path.some((node) =>
          node?.classList?.contains("forecast")
        );
        if (inEditor || !inForecast || event.button > 0) {
          tap = null;
          return;
        }
        tap = {
          pointerId: event.pointerId,
          x: event.clientX,
          y: event.clientY,
        };
      }, true);
      card.addEventListener("pointerup", (event) => {
        if (!tap || tap.pointerId !== event.pointerId) return;
        const deltaX = event.clientX - tap.x;
        const deltaY = event.clientY - tap.y;
        const isTap = deltaX * deltaX + deltaY * deltaY <= 100;
        tap = null;
        if (!isTap) return;
        card.dispatchEvent(new CustomEvent("hass-more-info", {
          detail: { entityId: card._config?.entity },
          bubbles: true,
          composed: true,
        }));
      }, true);
      const cancelTap = () => { tap = null; };
      card.addEventListener("pointercancel", cancelTap, true);
      card.addEventListener("lostpointercapture", cancelTap, true);
    }

    const forecast = card._forecastEvent?.forecast;
    const root = card.shadowRoot;
    const items = root?.querySelectorAll(".forecast-item:not(.label-only)");
    if (!Array.isArray(forecast) || !items?.length) continue;

    let rows = Number(config.grid_options?.rows);
    if (!Number.isFinite(rows)) {
      const height = card.getBoundingClientRect().height;
      rows = height < 190 ? 3 : height < 245 ? 4 : height < 300 ? 5 : 6;
    }
    const level = rows <= 3 ? 3 : rows === 4 ? 4 : rows === 5 ? 5 : 6;

    if (!root.querySelector("#yahoo-dashboard-height-style")) {
      const style = document.createElement("style");
      style.id = "yahoo-dashboard-height-style";
      style.textContent = `
        .yahoo-dashboard-details {
          display: flex; flex-direction: column; align-items: center;
          gap: 1px; margin-top: 2px; min-width: 0;
          font-size: 10px; line-height: 13px; white-space: nowrap;
        }
        .forecast-item:not(.label-only) {
          padding-left: 4px !important; padding-right: 4px !important;
        }
        .yahoo-dashboard-probability {
          color: var(--primary-color); font-weight: 600;
        }
        .yahoo-dashboard-rain, .yahoo-dashboard-humidity,
        .yahoo-dashboard-direction, .yahoo-dashboard-speed {
          color: var(--secondary-text-color);
        }
        .yahoo-dashboard-wind {
          display: flex; flex-direction: column; align-items: center;
          justify-content: center; gap: 0; line-height: 12px;
        }
        .yahoo-dashboard-arrow {
          width: 7px; height: 10px; color: var(--primary-color);
          transform-origin: 50% 50%; flex: 0 0 10px;
        }
        .yahoo-dashboard-calm {
          display: block; width: 9px; height: 2px;
          margin: 4px 0; border-radius: 1px;
          background: var(--secondary-text-color); flex: 0 0 2px;
        }
      `;
      root.append(style);
    }

    const windUnit = state.attributes?.wind_speed_unit;
    items.forEach((item, index) => {
      let details = item.querySelector(":scope > .yahoo-dashboard-details");
      if (level === 3 || !forecast[index]) {
        details?.remove();
        return;
      }
      const data = forecast[index];
      const signature = [
        text.locale,
        level,
        data.precipitation_probability,
        data.precipitation,
        data.humidity,
        data.wind_bearing,
        data.wind_speed,
      ].join("|");
      if (details?.dataset.signature === signature) return;
      if (!details) {
        details = document.createElement("div");
        details.className = "yahoo-dashboard-details";
        item.append(details);
      }
      details.dataset.signature = signature;
      details.replaceChildren();

      const addValue = (className, text, title) => {
        const value = document.createElement("div");
        value.className = className;
        value.textContent = text;
        value.title = title;
        details.append(value);
      };

      const probability = data.precipitation_probability;
      addValue(
        "yahoo-dashboard-probability",
        probability == null ? "--%" : `${Math.round(probability)}%`,
        probability == null
          ? `${text.probability} ${text.unknown}`
          : `${text.probability} ${Math.round(probability)}%`
      );

      if (level >= 5) {
        const precipitation = data.precipitation;
        addValue(
          "yahoo-dashboard-rain",
          precipitation == null ? "--mm" : `${compactNumber(precipitation)}mm`,
          precipitation == null
            ? `${text.precipitation} ${text.unknown}`
            : `${text.precipitation} ${compactNumber(precipitation)}mm`
        );
        const humidity = data.humidity;
        addValue(
          "yahoo-dashboard-humidity",
          humidity == null ? "--%" : `${Math.round(humidity)}%`,
          humidity == null
            ? `${text.humidity} ${text.unknown}`
            : `${text.humidity} ${Math.round(humidity)}%`
        );
      }

      if (level >= 6) {
        const speed = data.wind_speed;
        const bearing = Number(data.wind_bearing);
        const speedMeters = speed == null
          ? null
          : windUnit === "km/h" ? Number(speed) / 3.6 : Number(speed);
        const wind = document.createElement("div");
        wind.className = "yahoo-dashboard-wind";
        if (speedMeters === 0) {
          const calm = document.createElement("span");
          calm.className = "yahoo-dashboard-calm";
          wind.append(calm);
        } else if (Number.isFinite(bearing)) {
          const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
          svg.setAttribute("viewBox", "0 0 24 36");
          svg.classList.add("yahoo-dashboard-arrow");
          svg.style.transform = `rotate(${bearing}deg)`;
          const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
          path.setAttribute("d", "M12 0 L24 36 L12 27 L0 36 Z");
          path.setAttribute("fill", "currentColor");
          svg.append(path);
          wind.append(svg);
        }
        const direction = document.createElement("span");
        direction.className = "yahoo-dashboard-direction";
        direction.textContent = speedMeters === 0
          ? text.calm
          : Number.isFinite(bearing)
            ? directions[Math.round(((bearing % 360) + 360) % 360 / 22.5) % 16]
            : "—";
        const speedValue = document.createElement("span");
        speedValue.className = "yahoo-dashboard-speed";
        speedValue.textContent = speedMeters == null ? "--m" : `${compactNumber(speedMeters)}m`;
        wind.append(direction, speedValue);
        details.append(wind);
      }
    });
  }
}

if (!window.__yahooWeatherTabOrderTimer) {
  window.__yahooWeatherTabOrderTimer = window.setInterval(
    () => {
      const roots = collectYahooWeatherRoots();
      reorderNativeWeatherTabs(roots);
      addNativeWeatherProbabilities(roots);
      enhanceDashboardWeatherCards(roots);
    },
    250
  );
}

window.customCards = window.customCards || [];
window.customCards.push({
  type: "yahoo-weather-card",
  name: "Yahoo Weather Detail Card",
  description: "Yahoo weather with true precipitation probability and draggable forecasts.",
});
