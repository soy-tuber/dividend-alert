"""高配当銘柄アラート - メインエントリーポイント"""

import logging
import time
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))

from fetch_tickers import fetch_tse_tickers
from scan_dividends import scan_all

THRESHOLD = 0.05  # 5.0%

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def _width(s: str) -> int:
    """全角2, 半角1で文字幅を計算"""
    import unicodedata
    w = 0
    for c in s:
        w += 2 if unicodedata.east_asian_width(c) in ("F", "W") else 1
    return w


def _pad(s: str, width: int) -> str:
    """全角考慮で右パディング"""
    return s + " " * (width - _width(s))


def _trunc(s: str, width: int) -> str:
    """全角考慮で切り詰め"""
    w = 0
    for i, c in enumerate(s):
        import unicodedata
        cw = 2 if unicodedata.east_asian_width(c) in ("F", "W") else 1
        if w + cw > width:
            return s[:i]
        w += cw
    return s


def build_text(stocks: list[dict], scan_info: dict) -> str:
    today = datetime.now(JST).strftime("%Y-%m-%d")
    NW, SW = 18, 16  # name width, sector width

    sep = f"+------+{'-'*(NW+2)}+{'-'*(SW+2)}+-------+---------+--------+"
    hdr = f"| code | {_pad('name', NW)} | {_pad('sector', SW)} | yield |   price |    div |"

    lines = []
    lines.append(f"  Dividend Alert  {today}")
    lines.append(f"  yield >= 5.0%: {len(stocks)} stocks")
    lines.append("")
    lines.append(sep)
    lines.append(hdr)
    lines.append(sep)
    for s in stocks:
        code = s["ticker"].replace(".T", "")
        name = _pad(_trunc(s["name"], NW), NW)
        sector = _pad(_trunc(s["sector"], SW), SW)
        y_pct = f"{s['dividend_yield'] * 100:5.2f}%"
        price = f"{s['price']:>7,.0f}"
        div = f"{s['annual_dividend']:>6,.1f}"
        lines.append(f"| {code} | {name} | {sector} | {y_pct} | {price} | {div} |")
    lines.append(sep)
    lines.append("")
    lines.append(f"  scanned: {scan_info['total']}  duration: {scan_info['duration']}")
    lines.append(f"  * trailing 12m actual / may include special dividends")
    lines.append("")

    return "\n".join(lines)


def main():
    start = time.time()

    tickers = fetch_tse_tickers()
    logger.info(f"対象銘柄数: {len(tickers)}")

    qualified = scan_all(tickers, threshold=THRESHOLD)

    duration = time.time() - start
    minutes = int(duration // 60)
    seconds = int(duration % 60)
    duration_str = f"{minutes}分{seconds}秒"

    logger.info(f"スキャン完了: {len(qualified)}銘柄が閾値以上 (所要時間: {duration_str})")

    if qualified:
        scan_info = {"total": len(tickers), "duration": duration_str}
        text = build_text(qualified, scan_info)
        with open("result.html", "w", encoding="utf-8") as f:
            f.write(f"<pre>{text}</pre>")

        today = datetime.now(JST).strftime("%Y-%m-%d")
        with open("subject.txt", "w", encoding="utf-8") as f:
            f.write(f"[配当アラート] {len(qualified)}件 ({today})")

        logger.info(f"result.html 出力完了 ({len(qualified)}銘柄)")
    else:
        logger.info("閾値以上の銘柄なし")
        with open("result.html", "w", encoding="utf-8") as f:
            f.write("")


if __name__ == "__main__":
    main()
