# Home Assistant Yahoo!日本天气

[English](README.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md)

这是一个非官方 Home Assistant 自定义集成，从 [Yahoo!天気・災害](https://weather.yahoo.co.jp/weather/) 获取日本市区町村天气预报。

> 本项目与 Yahoo Japan Corporation 没有隶属或官方合作关系。集成解析公开网页而不是官方 API，因此 Yahoo 修改网页结构后可能需要更新集成。

## 功能

- 地区向导：**都道府县 → 预报地区 → 市区町村**
- 添加后可以重新选择地区，并保留原有天气实体 ID
- 无需 API Key
- 当前天气采用最近的 Yahoo 3 小时预报时段
- 3 小时预报：天气、温度、湿度、降水量、风向和风速
- 8 天每日预报：最高/最低温度、降水概率
- 使用 Home Assistant 标准天气状态
- 简体中文、日文、英文三语界面
- 每 30 分钟更新一次
- 保留旧版 URL/YAML 导入兼容性
- 拒绝无效或过期的 Yahoo 页面，保留最后一次有效预报
- 提供不含地区信息的 Home Assistant 诊断

## 安装

### HACS 自定义仓库

1. 打开 Home Assistant 的 HACS。
2. 进入“自定义仓库”。
3. 添加：
   ```text
   https://github.com/lanpili/ha-yahoo-jp-weather
   ```
4. 类别选择“集成”。
5. 安装 **Yahoo! Japan Weather**，然后重启 Home Assistant。

### 手动安装

将：

```text
custom_components/yahoo_jp_weather
```

复制到：

```text
/config/custom_components/yahoo_jp_weather
```

然后重启 Home Assistant。

## 配置

1. 打开“设置 → 设备与服务”。
2. 点击“添加集成”。
3. 搜索 **Yahoo! Japan Weather**。
4. 依次选择都道府县、预报地区和市区町村。

每个市区町村会创建一个 `weather.*` 实体。需要多个地点时，可以再次添加集成。

如需更改已有地区，请打开该配置项的菜单并选择“**重新配置**”。当前地区会自动预选，修改后原有实体 ID 不变。

## 数据说明

| 数据 | 来源 |
|---|---|
| 当前天气、温度 | 最近的 Yahoo 3 小时预报 |
| 每小时预报 | Yahoo 3 小时预报，以 HA hourly 格式提供 |
| 每日预报 | 今天、明天及週間天気，最多 8 天 |
| 湿度 | 3 小时预报 |
| 降水 | 3 小时降水量；每日使用 Yahoo 公布的降水概率 |
| 风 | 3 小时预报中的风向和风速 |

这里的“当前温度”是预报值，不是本地气象站实测温度。

## 限制

- Yahoo! JAPAN 没有为此用途提供正式公开 API。
- 集成依赖 Yahoo!天気・災害当前网页结构。
- 请勿把 30 分钟更新间隔调得更短。
- Yahoo 提供的地区名为日文；标准天气状态由 HA 自动本地化。

## 可靠性、安全与隐私

- 新增或重新配置市区町村时，集成会在保存配置项**之前**请求并解析最终天气页。验证失败时，原地区配置完全不变。
- 旧版 URL、页面中发现的链接和最终天气页只允许使用 `weather.yahoo.co.jp` 上的 HTTPS 市区町村页面；跨站重定向会被拒绝。
- 发布时间缺失或过旧、预报全部过期、预报表无有效数据或数值明显异常时，本次更新会失败并保留旧数据。
- Home Assistant 每 30 分钟抓取时，Yahoo 可以看到您的公网 IP、所选市区町村页面、请求时间和集成 User-Agent。
- 集成不会保存下载的完整 HTML。Home Assistant 诊断不会包含市区町村名称、来源 URL 或具体预报内容。

## 故障排查

1. 更新到最新集成版本并重启 Home Assistant。
2. 打开“设置 → 设备与服务 → Yahoo! Japan Weather”，检查配置项是否显示重试或加载错误。
3. 从配置项下载诊断。诊断包含更新状态和预报数量，但不包含所选地区。
4. 检查 Home Assistant 日志中的 `yahoo_jp_weather`。解析错误可能表示 Yahoo 修改了网页结构，请提交已经脱敏的 Bug 报告。

## 开发测试

详细说明参见 [CONTRIBUTING.md](CONTRIBUTING.md)。

```bash
python -m pip install --requirement requirements-test.txt
pytest -q --cov=custom_components.yahoo_jp_weather --cov-report=term-missing
ruff check custom_components tests scripts
ruff format --check custom_components tests scripts
mypy custom_components/yahoo_jp_weather
```

## 许可证

MIT License，参见 [LICENSE](LICENSE)。
