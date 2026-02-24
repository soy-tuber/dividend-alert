"""13週・26週・52週安値アラート"""

import logging
import sys
from datetime import datetime, timezone, timedelta

import yfinance as yf

JST = timezone(timedelta(hours=9))
logger = logging.getLogger(__name__)

WATCHLIST = [
    {"code": "2674", "name": "ハードオフ"},
    {"code": "8291", "name": "日産東京販売HD"},
    {"code": "5869", "name": "早稲田学習研究会"},
    {"code": "2411", "name": "ゲンダイエージェンシー"},
]

PERIODS = [
    ("13w", 91),
    ("26w", 182),
    ("52w", 365),
]


def check_lows() -> list[dict]:
    tickers = [f"{s['code']}.T" for s in WATCHLIST]
    data = yf.download(tickers, period="1y", progress=False)

    results = []
    for s in WATCHLIST:
        sym = f"{s['code']}.T"
        try:
            if len(WATCHLIST) == 1:
                close = data["Close"].dropna()
            else:
                close = data[("Close", sym)].dropna()

            if len(close) == 0:
                continue

            current = float(close.iloc[-1])
            lows = {}
            for label, days in PERIODS:
                window = close.iloc[-days:] if len(close) >= days else close
                low = float(window.min())
                pct = (current - low) / low * 100
                lows[label] = {"low": low, "pct": pct}

            results.append({
                "code": s["code"],
                "name": s["name"],
                "price": current,
                "lows": lows,
            })
        except (KeyError, IndexError) as e:
            logger.warning(f"{sym}: {e}")

    return results


def build_text(stocks: list[dict]) -> str:
    now = datetime.now(JST).strftime("%Y-%m-%d %H:%M")

    lines = []
    lines.append(f"  Low Price Check  {now}")
    lines.append("")
    lines.append("+------+---------+---------+---------+---------+")
    lines.append("| code |   price |  13w lo |  26w lo |  52w lo |")
    lines.append("+------+---------+---------+---------+---------+")
    for s in stocks:
        code = s["code"]
        price = f"{s['price']:>7,.0f}"
        cols = []
        for label, _ in PERIODS:
            low = s["lows"][label]["low"]
            pct = s["lows"][label]["pct"]
            if pct < 1.0:
                cols.append(f"  *{low:,.0f}")  # near low
            else:
                cols.append(f"{low:>7,.0f}")
            # pad to 7 chars
        c13 = cols[0].rjust(7)
        c26 = cols[1].rjust(7)
        c52 = cols[2].rjust(7)
        lines.append(f"| {code} | {price} | {c13} | {c26} | {c52} |")
    lines.append("+------+---------+---------+---------+---------+")
    lines.append("  * = within 1% of period low")
    lines.append("")

    # detail section
    alerts = []
    for s in stocks:
        for label, _ in PERIODS:
            pct = s["lows"][label]["pct"]
            if pct < 1.0:
                alerts.append(f"  !! {s['code']} {s['name']} is within {pct:.1f}% of {label} low")
    if alerts:
        lines.append("  --- ALERTS ---")
        lines.extend(alerts)
    else:
        lines.append("  no alerts")
    lines.append("")

    return "\n".join(lines)


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    stocks = check_lows()
    text = build_text(stocks)
    has_alert = any(
        s["lows"][label]["pct"] < 1.0
        for s in stocks
        for label, _ in PERIODS
    )

    with open("lowcheck.html", "w", encoding="utf-8") as f:
        f.write(f"<pre>{text}</pre>")

    today = datetime.now(JST).strftime("%Y-%m-%d")
    prefix = "!!" if has_alert else ""
    with open("lowcheck_subject.txt", "w", encoding="utf-8") as f:
        f.write(f"[安値チェック]{prefix} ({today})")

    # output flag for workflow
    with open("lowcheck_flag.txt", "w") as f:
        f.write("1")

    logger.info(f"安値チェック完了: {'アラートあり' if has_alert else 'アラートなし'}")


if __name__ == "__main__":
    main()
