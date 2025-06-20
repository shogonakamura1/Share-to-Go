# Google Maps API設定ガイド

## 概要
Share-to-Goアプリケーションでは、Google Maps JavaScript APIを使用して乗降場所の選択機能を提供しています。

## 必要なAPI
以下のGoogle Maps APIを有効化する必要があります：

1. **Maps JavaScript API** - 地図表示機能
2. **Places API** - 住所検索・自動補完機能
3. **Geocoding API** - 座標変換機能

## 設定手順

### 1. Google Cloud Consoleでの設定

#### 1.1 プロジェクトの作成・選択
1. [Google Cloud Console](https://console.cloud.google.com/)にアクセス
2. 新しいプロジェクトを作成するか、既存のプロジェクトを選択

#### 1.2 APIの有効化
1. "APIとサービス"→"ライブラリ"に移動
2. 以下のAPIを検索して有効化：
   - Maps JavaScript API
   - Places API
   - Geocoding API

#### 1.3 APIキーの作成
1. "APIとサービス"→"認証情報"に移動
2. "認証情報を作成"→"APIキー"を選択
3. 生成されたAPIキーをコピー

#### 1.4 APIキーの制限設定（推奨）
1. 作成したAPIキーをクリック
2. "アプリケーションの制限"で"HTTPリファラー"を選択
3. 許可するドメインを追加（例：`localhost:8000/*`、`yourdomain.com/*`）

### 2. 環境変数の設定

#### 2.1 開発環境での設定
```bash
# macOS/Linux
export GOOGLE_MAPS_API_KEY="your_actual_api_key_here"

# Windows
set GOOGLE_MAPS_API_KEY=your_actual_api_key_here
```

#### 2.2 本番環境での設定
- サーバーの環境変数に設定
- または、.envファイルを使用（セキュリティに注意）

### 3. アプリケーションの確認

#### 3.1 設定の確認
`sharetogo/settings.py`で以下の設定が正しく読み込まれていることを確認：
```python
GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', 'YOUR_API_KEY_HERE')
GOOGLE_MAPS_ENABLED = GOOGLE_MAPS_API_KEY != 'YOUR_API_KEY_HERE'
```

#### 3.2 動作確認
1. アプリケーションを起動
2. 配車計画の詳細画面で"参加する"ボタンをクリック
3. 地図が表示され、場所選択機能が動作することを確認

## 機能一覧

### 地図機能
- インタラクティブな地図表示
- 地図クリックでの場所選択
- 現在地取得機能
- 住所の自動補完

### マーカー機能
- 緑マーカー：乗車場所
- 赤マーカー：降車場所
- マーカーのドラッグ＆ドロップ（将来実装予定）

### 検索機能
- 住所の自動補完
- 座標から住所への変換
- 住所から座標への変換

## トラブルシューティング

### よくある問題

#### 1. 地図が表示されない
- APIキーが正しく設定されているか確認
- 必要なAPIが有効化されているか確認
- ブラウザのコンソールでエラーメッセージを確認

#### 2. 住所検索が動作しない
- Places APIが有効化されているか確認
- APIキーの制限設定を確認

#### 3. 現在地取得が動作しない
- HTTPS環境でない場合、ブラウザが位置情報を許可しない可能性
- ブラウザの位置情報許可設定を確認

### エラーメッセージ

#### "Google Maps APIキーが設定されていません"
- 環境変数`GOOGLE_MAPS_API_KEY`が設定されていない
- 設定後、アプリケーションを再起動

#### "このAPIキーは無効です"
- APIキーが正しくない
- 必要なAPIが有効化されていない
- APIキーの制限設定を確認

## 料金について

Google Maps APIは使用量に応じて課金されます：
- 月間の無料枠があります
- 詳細は[Google Maps Platform料金](https://cloud.google.com/maps-platform/pricing)を確認

## セキュリティ注意事項

1. **APIキーの保護**
   - APIキーをソースコードに直接記述しない
   - 環境変数または安全な設定管理システムを使用

2. **ドメイン制限**
   - APIキーにドメイン制限を設定
   - 不要なドメインからのアクセスを防ぐ

3. **使用量監視**
   - Google Cloud Consoleで使用量を定期的に確認
   - 異常な使用量がないか監視

## サポート

問題が解決しない場合は、以下を確認してください：
1. Google Cloud Consoleのログ
2. ブラウザの開発者ツールのコンソール
3. Djangoアプリケーションのログ 