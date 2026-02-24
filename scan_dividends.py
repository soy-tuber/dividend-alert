"""yfinanceで配当利回りをスキャン"""

import logging
import time

import yfinance as yf

logger = logging.getLogger(__name__)

BATCH_SIZE = 100
SLEEP_BETWEEN_BATCHES = 2.0
FALLBACK_SLEEP = 0.5


def scan_all(tickers: list[dict], threshold: float = 0.05) -> list[dict]:
    """全銘柄の配当利回りをスキャンし、閾値以上の銘柄を返す。

    Args:
        tickers: fetch_tickers.pyの出力 [{"ticker": "7203.T", "name": ..., "sector": ...}]
        threshold: 配当利回り閾値（デフォルト5.0%）

    Returns:
        list[dict]: 閾値以上の銘柄リスト（利回り降順）
    """
    ticker_map = {t["ticker"]: t for t in tickers}
    symbols = [t["ticker"] for t in tickers]

    # Phase 1: バッチダウンロード
    logger.info(f"Phase 1: {len(symbols)}銘柄をバッチスキャン中...")
    results = {}
    failed = []

    for i in range(0, len(symbols), BATCH_SIZE):
        batch = symbols[i : i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (len(symbols) + BATCH_SIZE - 1) // BATCH_SIZE
        logger.info(f"  バッチ {batch_num}/{total_batches} ({len(batch)}銘柄)")

        try:
            data = yf.download(
                batch,
                period="1y",
                auto_adjust=False,
                actions=True,
                group_by="ticker",
                threads=True,
                progress=False,
            )

            for sym in batch:
                try:
                    if len(batch) == 1:
                        divs = data["Dividends"].dropna()
                        close = data["Close"].dropna()
                    else:
                        divs = data[(sym, "Dividends")].dropna()
                        close = data[(sym, "Close")].dropna()

                    if len(close) == 0:
                        failed.append(sym)
                        continue

                    annual_div = divs.sum()
                    current_price = close.iloc[-1]

                    if current_price > 0 and annual_div > 0:
                        results[sym] = {
                            "dividend_yield": float(annual_div / current_price),
                            "annual_dividend": float(annual_div),
                            "price": float(current_price),
                        }
                    else:
                        results[sym] = None
                except (KeyError, IndexError):
                    failed.append(sym)

        except Exception as e:
            logger.warning(f"  バッチダウンロード失敗: {e}")
            failed.extend(batch)

        if i + BATCH_SIZE < len(symbols):
            time.sleep(SLEEP_BETWEEN_BATCHES)

    logger.info(f"Phase 1完了: {len(results)}件成功, {len(failed)}件失敗")

    # Phase 2: 失敗銘柄のフォールバック
    if failed:
        logger.info(f"Phase 2: {len(failed)}銘柄をフォールバックスキャン中...")
        for sym in failed:
            try:
                t = yf.Ticker(sym)
                info = t.info
                y = info.get("trailingAnnualDividendYield")
                if not y or y <= 0:
                    y = info.get("dividendYield")
                if not y or y <= 0:
                    rate = info.get("trailingAnnualDividendRate")
                    price = info.get("regularMarketPrice") or info.get("currentPrice")
                    if rate and price and price > 0:
                        y = rate / price
                if y and y > 0:
                    price = info.get("regularMarketPrice") or info.get("currentPrice", 0)
                    results[sym] = {
                        "dividend_yield": float(y),
                        "annual_dividend": float(info.get("trailingAnnualDividendRate", 0)),
                        "price": float(price) if price else 0,
                    }
                time.sleep(FALLBACK_SLEEP)
            except Exception:
                pass

    # フィルタリング
    qualified = []
    for sym, data in results.items():
        if data and data["dividend_yield"] >= threshold:
            info = ticker_map.get(sym, {})
            qualified.append({
                "ticker": sym,
                "name": info.get("name", ""),
                "sector": info.get("sector", ""),
                "dividend_yield": data["dividend_yield"],
                "annual_dividend": data["annual_dividend"],
                "price": data["price"],
            })

    qualified.sort(key=lambda x: x["dividend_yield"], reverse=True)
    logger.info(f"閾値{threshold*100:.1f}%以上: {len(qualified)}銘柄")
    return qualified
