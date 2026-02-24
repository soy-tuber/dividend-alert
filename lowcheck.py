"""13週・26週・52週安値スクリーニング（東証全銘柄）"""

import logging
import time
import unicodedata
from datetime import datetime, timezone, timedelta

import yfinance as yf

from fetch_tickers import fetch_tse_tickers

JST = timezone(timedelta(hours=9))
logger = logging.getLogger(__name__)

PERIODS = [
    ("13w", 91),
    ("26w", 182),
    ("52w", 365),
]

BATCH_SIZE = 100
SLEEP_BETWEEN = 2.0
NEAR_LOW_PCT = 1.0  # 安値から1%以内でアラート


def scan_lows(tickers: list[dict]) -> list[dict]:
    """全銘柄の安値近接チェック。安値1%以内の銘柄のみ返す。"""
    ticker_map = {t["ticker"]: t for t in tickers}
    symbols = [t["ticker"] for t in tickers]
    results = []

    for i in range(0, len(symbols), BATCH_SIZE):
        batch = symbols[i : i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (len(symbols) + BATCH_SIZE - 1) // BATCH_SIZE
        logger.info(f"  batch {batch_num}/{total_batches} ({len(batch)})")

        try:
            data = yf.download(
                batch, period="1y", auto_adjust=False,
                group_by="ticker", threads=True, progress=False,
            )

            for sym in batch:
                try:
                    if len(batch) == 1:
                        close = data["Close"].dropna()
                    else:
                        close = data[(sym, "Close")].dropna()

                    if len(close) < 10:
                        continue

                    current = float(close.iloc[-1])
                    lows = {}
                    near_any = False
                    for label, days in PERIODS:
                        window = close.iloc[-days:] if len(close) >= days else close
                        low = float(window.min())
                        pct = (current - low) / low * 100 if low > 0 else 999
                        lows[label] = {"low": low, "pct": pct}
                        if pct < NEAR_LOW_PCT:
                            near_any = True

                    if near_any:
                        info = ticker_map.get(sym, {})
                        results.append({
                            "code": sym.replace(".T", ""),
                            "name": info.get("name", ""),
                            "price": current,
                            "lows": lows,
                        })
                except (KeyError, IndexError):
                    pass

        except Exception as e:
            logger.warning(f"  batch failed: {e}")

        if i + BATCH_SIZE < len(symbols):
            time.sleep(SLEEP_BETWEEN)

    # 52w安値に近い順でソート
    results.sort(key=lambda x: x["lows"]["52w"]["pct"])
    return results


def _width(s: str) -> int:
    return sum(2 if unicodedata.east_asian_width(c) in ("F", "W") else 1 for c in s)


def _pad(s: str, w: int) -> str:
    return s + " " * (w - _width(s))


def _trunc(s: str, w: int) -> str:
    cur = 0
    for i, c in enumerate(s):
        cw = 2 if unicodedata.east_asian_width(c) in ("F", "W") else 1
        if cur + cw > w:
            return s[:i]
        cur += cw
    return s


NW = 16


def build_text(stocks: list[dict], scan_info: dict) -> str:
    now = datetime.now(JST).strftime("%Y-%m-%d %H:%M")

    sep = f"+------+{'-'*(NW+2)}+---------+---------+---------+---------+"
    hdr = f"| code | {_pad('name', NW)} |   price |  13w lo |  26w lo |  52w lo |"

    lines = []
    lines.append(f"  Low Price Screener  {now}")
    lines.append(f"  within {NEAR_LOW_PCT:.0f}% of period low: {len(stocks)} stocks")
    lines.append("")
    lines.append(sep)
    lines.append(hdr)
    lines.append(sep)
    for s in stocks:
        name = _pad(_trunc(s["name"], NW), NW)
        price = f"{s['price']:>7,.0f}"
        cols = []
        for label, _ in PERIODS:
            low = s["lows"][label]["low"]
            pct = s["lows"][label]["pct"]
            if pct < NEAR_LOW_PCT:
                cols.append(f"  *{low:,.0f}")
            else:
                cols.append(f"{low:>7,.0f}")
        c13 = cols[0].rjust(7)
        c26 = cols[1].rjust(7)
        c52 = cols[2].rjust(7)
        lines.append(f"| {s['code']} | {name} | {price} | {c13} | {c26} | {c52} |")
    lines.append(sep)
    lines.append("  * = within 1% of period low")
    lines.append("")
    lines.append(f"  scanned: {scan_info['total']}  duration: {scan_info['duration']}")
    lines.append("")

    return "\n".join(lines)


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    start = time.time()

    tickers = fetch_tse_tickers()
    logger.info(f"対象: {len(tickers)}銘柄")

    stocks = scan_lows(tickers)

    duration = time.time() - start
    m, s = int(duration // 60), int(duration % 60)
    duration_str = f"{m}m{s}s"

    logger.info(f"安値近接: {len(stocks)}銘柄 ({duration_str})")

    scan_info = {"total": len(tickers), "duration": duration_str}
    text = build_text(stocks, scan_info)

    with open("lowcheck.html", "w", encoding="utf-8") as f:
        f.write(f"<pre>{text}</pre>")

    today = datetime.now(JST).strftime("%Y-%m-%d")
    mark = "!!" if stocks else ""
    with open("lowcheck_subject.txt", "w", encoding="utf-8") as f:
        f.write(f"[安値スクリーニング]{mark} {len(stocks)}件 ({today})")

    with open("lowcheck_flag.txt", "w") as f:
        f.write("1" if stocks else "")


if __name__ == "__main__":
    main()
