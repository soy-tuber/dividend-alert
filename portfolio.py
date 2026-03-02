"""保有銘柄の時価モニタリング"""

import logging
import sys
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))

import yfinance as yf

logger = logging.getLogger(__name__)

PORTFOLIO = [
    {"code": "2674", "shares": 15000},
    {"code": "8291", "shares": 50000},
    {"code": "5869", "shares": 20000},
    {"code": "2411", "shares": 35000},
]


def fetch_prices() -> list[dict]:
    tickers = [f"{h['code']}.T" for h in PORTFOLIO]
    data = yf.download(tickers, period="5d", progress=False)

    results = []
    for h in PORTFOLIO:
        sym = f"{h['code']}.T"
        try:
            if len(PORTFOLIO) == 1:
                closes = data["Close"].dropna()
            else:
                closes = data[("Close", sym)].dropna()
            price = float(closes.iloc[-1])
            prev = float(closes.iloc[-2]) if len(closes) >= 2 else price
            change_pct = (price - prev) / prev * 100 if prev > 0 else 0
            results.append({
                "code": h["code"],
                "shares": h["shares"],
                "price": price,
                "value": price * h["shares"],
                "change_pct": change_pct,
            })
        except (KeyError, IndexError) as e:
            logger.warning(f"{sym} 取得失敗: {e}")
            results.append({"code": h["code"], "shares": h["shares"], "price": 0, "value": 0, "change_pct": 0})

    return results


def build_text(stocks: list[dict], session: str) -> str:
    now = datetime.now(JST).strftime("%Y-%m-%d %H:%M")
    total = sum(s["value"] for s in stocks)

    lines = []
    lines.append(f"  {session}  {now}")
    lines.append("")
    lines.append("+------+---------+--------+---------------+")
    lines.append("| code |  shares | 前日比 |         value |")
    lines.append("+------+---------+--------+---------------+")
    for s in stocks:
        code = s["code"]
        shares = f"{s['shares']:>7,}"
        chg = f"{s['change_pct']:+.1f}%"
        chg = f"{chg:>6}"
        value = f"{s['value']:>13,.0f}"
        lines.append(f"| {code} | {shares} | {chg} | {value} |")
    lines.append("+------+---------+--------+---------------+")
    lines.append(f"  TOTAL                     {total:>13,.0f}")
    lines.append("")

    return "\n".join(lines)


def main(session: str):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    stocks = fetch_prices()
    text = build_text(stocks, session)

    with open("portfolio.html", "w", encoding="utf-8") as f:
        f.write(f"<pre>{text}</pre>")

    today = datetime.now(JST).strftime("%Y-%m-%d")
    with open("portfolio_subject.txt", "w", encoding="utf-8") as f:
        f.write(f"[時価] {session} ({today})")

    total = sum(s["value"] for s in stocks)
    logger.info(f"{session}: 合計時価 {total:,.0f}円")

    from store import save_portfolio
    save_portfolio(stocks, session)


if __name__ == "__main__":
    session = sys.argv[1] if len(sys.argv) > 1 else "テスト"
    main(session)
