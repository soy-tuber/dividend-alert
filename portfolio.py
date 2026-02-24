"""保有銘柄の時価モニタリング"""

import logging
from datetime import datetime

import yfinance as yf

logger = logging.getLogger(__name__)

PORTFOLIO = [
    {"code": "2674", "name": "ハードオフコーポレーション", "shares": 15000},
    {"code": "8291", "name": "日産東京販売ホールディングス", "shares": 50000},
    {"code": "5869", "name": "早稲田学習研究会", "shares": 20000},
    {"code": "2411", "name": "ゲンダイエージェンシー", "shares": 35000},
]


def fetch_prices() -> list[dict]:
    """保有銘柄の現在値を取得"""
    tickers = [f"{h['code']}.T" for h in PORTFOLIO]
    data = yf.download(tickers, period="1d", progress=False)

    results = []
    for h in PORTFOLIO:
        sym = f"{h['code']}.T"
        try:
            if len(PORTFOLIO) == 1:
                price = float(data["Close"].dropna().iloc[-1])
            else:
                price = float(data[("Close", sym)].dropna().iloc[-1])
            value = price * h["shares"]
            results.append({
                "code": h["code"],
                "name": h["name"],
                "shares": h["shares"],
                "price": price,
                "value": value,
            })
        except (KeyError, IndexError) as e:
            logger.warning(f"{sym} 取得失敗: {e}")
            results.append({
                "code": h["code"],
                "name": h["name"],
                "shares": h["shares"],
                "price": 0,
                "value": 0,
            })

    return results


def build_html(stocks: list[dict], session: str) -> str:
    now = datetime.now().strftime("%Y年%m月%d日 %H:%M")
    total_value = sum(s["value"] for s in stocks)

    rows = ""
    for s in stocks:
        price = f"{s['price']:,.0f}"
        value = f"{s['value']:,.0f}"
        rows += f"""
        <tr>
          <td style="padding:6px 12px;border:1px solid #ddd">{s['code']}</td>
          <td style="padding:6px 12px;border:1px solid #ddd">{s['name']}</td>
          <td style="padding:6px 12px;border:1px solid #ddd;text-align:right">{s['shares']:,}</td>
          <td style="padding:6px 12px;border:1px solid #ddd;text-align:right;font-weight:bold">{price}円</td>
          <td style="padding:6px 12px;border:1px solid #ddd;text-align:right">{value}円</td>
        </tr>"""

    return f"""
    <div style="font-family:sans-serif;max-width:700px;margin:0 auto">
      <h2 style="color:#2e7d32">保有銘柄レポート - {session}</h2>
      <p style="color:#666">{now}</p>

      <table style="border-collapse:collapse;width:100%;font-size:14px">
        <thead>
          <tr style="background:#2e7d32;color:#fff">
            <th style="padding:8px 12px;text-align:left">コード</th>
            <th style="padding:8px 12px;text-align:left">銘柄名</th>
            <th style="padding:8px 12px;text-align:right">保有数</th>
            <th style="padding:8px 12px;text-align:right">現在値</th>
            <th style="padding:8px 12px;text-align:right">時価</th>
          </tr>
        </thead>
        <tbody>
          {rows}
        </tbody>
        <tfoot>
          <tr style="background:#e8f5e9;font-weight:bold">
            <td colspan="4" style="padding:8px 12px;border:1px solid #ddd;text-align:right">合計時価</td>
            <td style="padding:8px 12px;border:1px solid #ddd;text-align:right;font-size:16px">{total_value:,.0f}円</td>
          </tr>
        </tfoot>
      </table>
    </div>
    """


def main(session: str):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    stocks = fetch_prices()
    html = build_html(stocks, session)

    with open("portfolio.html", "w", encoding="utf-8") as f:
        f.write(html)

    today = datetime.now().strftime("%Y-%m-%d")
    with open("portfolio_subject.txt", "w", encoding="utf-8") as f:
        f.write(f"[時価レポート] {session} ({today})")

    total = sum(s["value"] for s in stocks)
    logger.info(f"{session}: 合計時価 {total:,.0f}円")


if __name__ == "__main__":
    import sys
    session = sys.argv[1] if len(sys.argv) > 1 else "テスト"
    main(session)
