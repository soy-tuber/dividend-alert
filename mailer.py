"""Gmail API でメール送信"""

import base64
import logging
import os
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def _build_service():
    creds = Credentials(
        token=None,
        refresh_token=os.environ["GMAIL_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GMAIL_CLIENT_ID"],
        client_secret=os.environ["GMAIL_CLIENT_SECRET"],
        scopes=SCOPES,
    )
    creds.refresh(Request())
    return build("gmail", "v1", credentials=creds)


def _build_html(stocks: list[dict], scan_info: dict) -> str:
    today = datetime.now().strftime("%Y年%m月%d日")

    rows = ""
    for s in stocks:
        y_pct = f"{s['dividend_yield'] * 100:.2f}%"
        price = f"{s['price']:,.0f}"
        div = f"{s['annual_dividend']:,.1f}"
        rows += f"""
        <tr>
          <td style="padding:6px 12px;border:1px solid #ddd">{s['ticker'].replace('.T','')}</td>
          <td style="padding:6px 12px;border:1px solid #ddd">{s['name']}</td>
          <td style="padding:6px 12px;border:1px solid #ddd">{s['sector']}</td>
          <td style="padding:6px 12px;border:1px solid #ddd;text-align:right;font-weight:bold;color:#d32f2f">{y_pct}</td>
          <td style="padding:6px 12px;border:1px solid #ddd;text-align:right">{price}円</td>
          <td style="padding:6px 12px;border:1px solid #ddd;text-align:right">{div}円</td>
        </tr>"""

    return f"""
    <div style="font-family:sans-serif;max-width:800px;margin:0 auto">
      <h2 style="color:#1565c0">高配当銘柄アラート - {today}</h2>
      <p>配当利回り <strong>5.0%以上</strong> の東証上場銘柄: <strong>{len(stocks)}件</strong></p>

      <table style="border-collapse:collapse;width:100%;font-size:14px">
        <thead>
          <tr style="background:#1565c0;color:#fff">
            <th style="padding:8px 12px;text-align:left">コード</th>
            <th style="padding:8px 12px;text-align:left">銘柄名</th>
            <th style="padding:8px 12px;text-align:left">セクター</th>
            <th style="padding:8px 12px;text-align:right">配当利回り</th>
            <th style="padding:8px 12px;text-align:right">株価</th>
            <th style="padding:8px 12px;text-align:right">年間配当</th>
          </tr>
        </thead>
        <tbody>
          {rows}
        </tbody>
      </table>

      <div style="margin-top:20px;padding:12px;background:#f5f5f5;border-radius:4px;font-size:13px;color:#666">
        <p style="margin:4px 0">スキャン銘柄数: {scan_info['total']}</p>
        <p style="margin:4px 0">所要時間: {scan_info['duration']}</p>
        <p style="margin:4px 0;color:#999">※ 配当利回りはyfinanceの過去12ヶ月実績値です。特別配当を含む場合があります。</p>
        <p style="margin:4px 0;color:#999">※ 投資判断は自己責任でお願いします。</p>
      </div>
    </div>
    """


def send_alert(stocks: list[dict], scan_info: dict):
    sender = os.environ["GMAIL_SENDER"]
    recipient = os.environ["GMAIL_RECIPIENT"]
    today = datetime.now().strftime("%Y-%m-%d")

    subject = f"[配当アラート] 高配当銘柄 {len(stocks)}件 ({today})"
    html = _build_html(stocks, scan_info)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    msg.attach(MIMEText(html, "html", "utf-8"))

    service = _build_service()
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    service.users().messages().send(userId="me", body={"raw": raw}).execute()
    logger.info(f"メール送信完了: {recipient}")
