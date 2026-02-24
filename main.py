"""高配当銘柄アラート - メインエントリーポイント"""

import logging
import time
from datetime import datetime

from fetch_tickers import fetch_tse_tickers
from scan_dividends import scan_all

THRESHOLD = 0.05  # 5.0%

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def build_html(stocks: list[dict], scan_info: dict) -> str:
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


def main():
    start = time.time()

    # 1. JPX銘柄リスト取得
    tickers = fetch_tse_tickers()
    logger.info(f"対象銘柄数: {len(tickers)}")

    # 2. 配当利回りスキャン
    qualified = scan_all(tickers, threshold=THRESHOLD)

    duration = time.time() - start
    minutes = int(duration // 60)
    seconds = int(duration % 60)
    duration_str = f"{minutes}分{seconds}秒"

    logger.info(f"スキャン完了: {len(qualified)}銘柄が閾値以上 (所要時間: {duration_str})")

    # 3. HTML出力（GitHub Actionがメール送信）
    if qualified:
        scan_info = {"total": len(tickers), "duration": duration_str}
        html = build_html(qualified, scan_info)
        with open("result.html", "w", encoding="utf-8") as f:
            f.write(html)

        today = datetime.now().strftime("%Y-%m-%d")
        with open("subject.txt", "w", encoding="utf-8") as f:
            f.write(f"[配当アラート] 高配当銘柄 {len(qualified)}件 ({today})")

        logger.info(f"result.html 出力完了 ({len(qualified)}銘柄)")
    else:
        logger.info("閾値以上の銘柄なし")
        with open("result.html", "w", encoding="utf-8") as f:
            f.write("")


if __name__ == "__main__":
    main()
