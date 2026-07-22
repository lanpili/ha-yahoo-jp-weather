# Home Assistant Yahoo!天気

[English](README.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md)

[Yahoo!天気・災害](https://weather.yahoo.co.jp/weather/)の市区町村別予報をHome Assistantで利用するための非公式カスタムインテグレーションです。

> 本プロジェクトはYahoo Japan株式会社との提携・公式関係はありません。公式APIではなく公開Webページを解析するため、Yahoo側のHTML変更により更新が必要になる場合があります。

## 主な機能

- 地域選択ウィザード：**都道府県 → 予報地域 → 市区町村**
- 追加後も地域を再設定でき、既存の天気エンティティIDを維持
- APIキー不要
- Yahooの直近3時間予報を現在の天気として表示
- 3時間予報：天気、気温、湿度、降水量、風向、風速
- 8日間の日別予報：最高/最低気温、降水確率
- Home Assistant標準の天気状態に対応
- 日本語、英語、簡体字中国語のUI翻訳
- 30分ごとの更新
- 旧URL/YAMLインポートとの互換性を維持

## インストール

### HACSカスタムリポジトリ

1. Home AssistantでHACSを開きます。
2. 「カスタムリポジトリ」を開きます。
3. 次のURLを追加します。
   ```text
   https://github.com/lanpili/ha-yahoo-jp-weather
   ```
4. カテゴリは「Integration」を選択します。
5. **Yahoo! Japan Weather**をインストールし、Home Assistantを再起動します。

### 手動インストール

```text
custom_components/yahoo_jp_weather
```

を次の場所へコピーします。

```text
/config/custom_components/yahoo_jp_weather
```

その後、Home Assistantを再起動してください。

## 設定

1. 「設定 → デバイスとサービス」を開きます。
2. 「統合を追加」を選択します。
3. **Yahoo! Japan Weather**を検索します。
4. 都道府県、予報地域、市区町村を順番に選択します。

市区町村ごとに`weather.*`エンティティが1つ作成されます。複数地点を追加する場合は、設定フローを再度実行してください。

既存の地域を変更するには、設定エントリのメニューから「**再設定**」を選択します。現在の地域が初期選択され、変更後も既存のエンティティIDは維持されます。

## データについて

| データ | 内容 |
|---|---|
| 現在の天気・気温 | 直近のYahoo 3時間予報 |
| 時間別予報 | Yahooの3時間予報をHA hourly形式で提供 |
| 日別予報 | 今日、明日、週間天気を合わせて最大8日 |
| 湿度 | 3時間予報 |
| 降水 | 3時間降水量、日別は公表された降水確率 |
| 風 | 3時間予報の風向・風速 |

「現在の気温」は観測所の実測値ではなく予報値です。

## 制限事項

- この用途向けのYahoo! JAPAN公式公開APIはありません。
- Yahoo!天気・災害のHTML構造に依存しています。
- 30分より短い更新間隔に変更しないでください。
- 地域名はYahooが提供する日本語表記です。標準天気状態はHome Assistantがローカライズします。

## 開発・テスト

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q custom_components
```

## ライセンス

MIT License。詳細は[LICENSE](LICENSE)をご覧ください。
