"""Gmail OAuth ワンタイム認証スクリプト（ローカルで1回だけ実行）

使い方:
  1. Google Cloud Console で OAuth 2.0 クライアントID を作成（デスクトップアプリ）
  2. client_secret.json をこのディレクトリに配置
  3. uv run python setup_gmail.py を実行
  4. ブラウザで認証
  5. 表示される REFRESH_TOKEN を GitHub Secrets に設定
"""

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def main():
    flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
    creds = flow.run_local_server(port=0)

    print()
    print("=" * 60)
    print("認証成功！以下をGitHub Secretsに設定してください:")
    print("=" * 60)
    print(f"GMAIL_CLIENT_ID     = {creds.client_id}")
    print(f"GMAIL_CLIENT_SECRET = {creds.client_secret}")
    print(f"GMAIL_REFRESH_TOKEN = {creds.refresh_token}")
    print("=" * 60)


if __name__ == "__main__":
    main()
