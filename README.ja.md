# Home Assistant Yahoo!天気

[English](README.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md)

[Yahoo!天気・災害](https://weather.yahoo.co.jp/weather/)とYahoo天気アプリの1時間予報データをHome Assistantで利用するための非公式カスタムインテグレーションです。

> 本プロジェクトはYahoo Japan株式会社との提携・公式関係はありません。この用途向けの公式公開APIはなく、公開地域ページとYahoo天気アプリが使用するデータエンドポイントを利用するため、上流の変更により更新が必要になる場合があります。

## 主な機能

- 地域選択ウィザード：**都道府県 → 予報地域 → 市区町村**
- 追加後も地域を再設定でき、既存の天気エンティティIDを維持
- APIキー不要
- Yahooの直近1時間予報を現在の天気として表示
- 実際の1時間予報：天気、気温、降水確率、湿度、降水量、風向、風速
- 最大10日間の日別予報：最高/最低気温、降水確率
- Yahoo風の時間別詳細を表示するオプションの高さ対応ダッシュボード拡張
- Home Assistant標準の天気状態に対応
- 日本語、英語、簡体字中国語のUI翻訳
- 30分ごとの更新
- 旧URL/YAMLインポートとの互換性を維持
- 無効または古いYahooページを拒否し、最後に有効だった予報を保持
- 地域情報を含まないHome Assistant診断

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

### オプションの高さ対応ダッシュボード拡張

このファイルを導入しなくても、インテグレーション本体とHA標準天気カードは動作します。標準の `weather-forecast` カードで、高さに応じた時間別詳細を表示する場合：

1. [`dashboard/yahoo-weather-card.js`](dashboard/yahoo-weather-card.js) を次へコピーします。
   ```text
   /config/www/yahoo-weather-card.js
   ```
2. 「**設定 → ダッシュボード → リソース**」にJavaScriptモジュールを追加します。
   ```text
   /local/yahoo-weather-card.js?v=2.2.1
   ```
3. フロントエンドを再読み込みするか、Home Assistantアプリを完全に終了して開き直します。

HA標準の天気予報カードをそのまま使用してください。このリソースはYahooの帰属表示を持つ天気エンティティを識別し、セクショングリッドの高さに応じて表示を変更します。

- 3行：時刻、天気アイコン、気温
- 4行：降水確率を追加
- 5行：降水量と湿度を追加
- 6行以上：Yahoo風の風向矢印、風向、風速を追加

390px幅のモバイルレイアウトでも6時間以上を完全表示します。中国語・日本語・英語で同じレイアウトを維持し、Home Assistantの現在の表示言語へ自動的に追従します。ドラッグしていない部分をタップすると天気詳細を開き、横方向の予報ドラッグも維持します。このオプション拡張はHAフロントエンドの内部構造に依存するため、大幅なUI変更後に更新が必要な場合があります。HACSがインストールするのはインテグレーション本体のみで、このダッシュボードリソースは自動インストールされません。

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
| 現在の天気・気温 | 直近のYahoo 1時間予報 |
| 時間別予報 | Yahoo天気アプリの1時間予報 |
| 日別予報 | Yahoo天気アプリの日別予報（最大10日） |
| 湿度 | 1時間予報 |
| 降水 | 1時間降水量と降水確率、日別は公表された降水確率 |
| 風 | 1時間予報の風向・風速 |

「現在の気温」は観測所の実測値ではなく予報値です。

## 制限事項

- この用途向けのYahoo! JAPAN公式公開APIはありません。組み込みのアプリクライアント識別子はユーザーAPIキーではありません。
- Yahooの現在の地域ページ構造とアプリ予報レスポンス形式に依存しています。
- 30分より短い更新間隔に変更しないでください。
- 地域名はYahooが提供する日本語表記です。標準天気状態はHome Assistantがローカライズします。

## 信頼性・セキュリティ・プライバシー

- 新規追加または再設定する市区町村ページは、設定エントリを保存する**前**に取得・解析されます。検証に失敗した場合、既存の地域設定は変更されません。
- 旧URL、検出したリンク、最終地域ページは、`weather.yahoo.co.jp`上のHTTPS市区町村ページに限定されます。別サイトへのリダイレクトは拒否します。
- 公開時刻の欠落や古い予報、期限切れ予報、利用できないレスポンス、現実的でない数値は更新に使用しません。
- 30分ごとの取得時に、Yahoo側からは公開IPアドレス、選択した市区町村コード、アクセス時刻、User-Agentを確認できます。
- 取得したHTMLと予報レスポンスは保存しません。Home Assistant診断には市区町村名、取得元URL、予報内容を含めません。

## トラブルシューティング

1. 最新版へ更新し、Home Assistantを再起動します。
2. 「設定 → デバイスとサービス → Yahoo! Japan Weather」で再試行・セットアップエラーを確認します。
3. 設定エントリから診断をダウンロードします。更新状態と件数は含まれますが、選択地域は含まれません。
4. Home Assistantログの`yahoo_jp_weather`を確認します。解析エラーはYahooのHTML変更を示す場合があります。個人情報を削除してIssueを報告してください。

## 開発・テスト

詳細は[CONTRIBUTING.md](CONTRIBUTING.md)をご覧ください。

```bash
python -m pip install --requirement requirements-test.txt
pytest -q --cov=custom_components.yahoo_jp_weather --cov-report=term-missing
ruff check custom_components tests scripts
ruff format --check custom_components tests scripts
mypy custom_components/yahoo_jp_weather
```

## ライセンス

MIT License。詳細は[LICENSE](LICENSE)をご覧ください。
