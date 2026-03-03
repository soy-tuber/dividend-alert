# dividend-alert

東証上場銘柄の配当利回り・安値・ポートフォリオ時価をモニタリングし、メールで通知するシステム。

## アーキテクチャ

```
[ローカル PC]                    [GitHub Actions]
 crontab                          workflow_dispatch
   │  trigger.sh (curl)              │
   └──────────────────────────────►   ├─ Python スクレイピング
                                      ├─ HTML レポート生成
                                      └─ Gmail SMTP 送信
```

- **ローカル PC**: crontab で定時に GitHub API (`workflow_dispatch`) を叩くだけ
- **GitHub Actions**: データ取得・分析・メール送信を実行
- GitHub Actions の schedule cron はフォールバックとして残してある（PC 未起動時用）

## ワークフロー

| 時刻 (JST) | ワークフロー | 内容 | 曜日 |
|------------|-------------|------|------|
| 09:10 | portfolio.yml | ポートフォリオ時価（寄り付き） | 平日 |
| 12:40 | portfolio.yml | ポートフォリオ時価（後場寄り） | 平日 |
| 15:10 | lowcheck.yml | 26週・52週安値スクリーニング | 平日 |
| 15:40 | portfolio.yml | ポートフォリオ時価（終値） | 平日 |
| 13:40 | alert.yml | 高配当（利回り5%以上）アラート | 月曜 |

## セットアップ

### 1. GitHub Secrets

リポジトリの Settings > Secrets に以下を設定:

| Secret | 内容 |
|--------|------|
| `GMAIL_ADDRESS` | 送受信に使う Gmail アドレス |
| `GMAIL_APP_PASSWORD` | Gmail アプリパスワード |

### 2. ローカル cron トリガー（任意）

GitHub Actions の cron 遅延を回避するため、ローカル PC から `workflow_dispatch` で起動する。

1. **GitHub Fine-grained PAT を作成**
   - Settings > Developer settings > Fine-grained personal access tokens
   - Repository access: `soy-tuber/dividend-alert` のみ
   - Permissions: Actions (Read and Write)

2. **crontab に登録**
   ```bash
   crontab -e
   ```
   `crontab.example` の内容をコピペし、`GITHUB_PAT` を実際のトークンに書き換える。

3. **cron デーモンの起動**（Crostini 等で必要な場合）
   ```bash
   sudo apt-get install -y cron
   sudo /etc/init.d/cron start
   ```

### 3. 手動テスト

```bash
GITHUB_PAT=ghp_xxx ./trigger.sh portfolio.yml 手動テスト
```

GitHub Actions タブでワークフローが即座に起動することを確認。

## ファイル構成

```
dividend-alert/
├── .github/workflows/
│   ├── alert.yml          # 高配当アラート (月曜)
│   ├── lowcheck.yml       # 安値スクリーニング (平日)
│   └── portfolio.yml      # ポートフォリオ時価 (平日 3回)
├── main.py                # 配当スクリーナー本体
├── lowcheck.py            # 安値チェック本体
├── portfolio.py           # ポートフォリオモニター本体
├── scan_dividends.py      # 配当データ取得・計算
├── fetch_tickers.py       # JPX 銘柄リスト取得
├── store.py               # SQLite DB 永続化
├── textutil.py            # 全角幅ユーティリティ
├── trigger.sh             # ローカル cron → workflow_dispatch トリガー
├── crontab.example        # crontab 設定例
├── requirements.txt       # Python 依存パッケージ
├── pyproject.toml         # プロジェクト設定
└── .env.example           # 環境変数テンプレート
```

### GitHub Actions 上のみに存在するデータ

- **alerts.db** — SQLite データベース（Artifacts に保存、各 run 間で引き継ぎ）
- **\*.html / \*_subject.txt** — レポート生成物（run 内で一時生成）
