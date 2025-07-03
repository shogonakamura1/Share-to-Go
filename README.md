# Share-to-Go

配車計画を共有・管理するWebアプリケーションです。

## 機能

- 配車計画の作成・編集・削除
- 配車計画への参加・キャンセル
- 運転者モード（遅延情報の更新）
- 運行状況のリアルタイム表示
- ユーザー管理（登録・ログイン）

## 技術スタック

- **Backend**: Django 5.2.3
- **Database**: PostgreSQL (Heroku), SQLite (開発)
- **Frontend**: Bootstrap 5, HTML, CSS, JavaScript
- **Deployment**: Heroku

## セットアップ

### ローカル開発

1. リポジトリをクローン
```bash
git clone <repository-url>
cd Share-to-Go
```

2. 仮想環境を作成・アクティベート
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. 依存関係をインストール
```bash
pip install -r requirements.txt
```

4. データベースをマイグレート
```bash
python manage.py migrate
```

5. 開発サーバーを起動
```bash
python manage.py runserver
```

### 環境変数

以下の環境変数を設定してください：

- `SECRET_KEY`: Djangoのシークレットキー
- `DEBUG`: デバッグモード（True/False）
- `DATABASE_URL`: データベースURL（Heroku用）
- `GOOGLE_MAPS_API_KEY`: Google Maps APIキー（オプション）

## デプロイ

### Heroku

1. Heroku CLIをインストール
2. Herokuアプリを作成
```bash
heroku create your-app-name
```

3. 環境変数を設定
```bash
heroku config:set SECRET_KEY=your-secret-key
heroku config:set DEBUG=False
```

4. データベースを追加
```bash
heroku addons:create heroku-postgresql:mini
```

5. デプロイ
```bash
git push heroku main
```

6. マイグレーションを実行
```bash
heroku run python manage.py migrate
```

## 使用方法

1. ユーザー登録・ログイン
2. 配車計画を作成
3. 他のユーザーの配車計画に参加
4. 運転者モードで運行状況を更新

## ライセンス

MIT License 