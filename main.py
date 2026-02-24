"""高配当銘柄アラート - メインエントリーポイント"""

import logging
import time

from dotenv import load_dotenv

from fetch_tickers import fetch_tse_tickers
from mailer import send_alert
from scan_dividends import scan_all

load_dotenv()

THRESHOLD = 0.05  # 5.0%

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


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

    # 3. メール送信
    if qualified:
        scan_info = {"total": len(tickers), "duration": duration_str}
        send_alert(qualified, scan_info)
        logger.info("アラートメール送信完了")
    else:
        logger.info("閾値以上の銘柄なし - メール送信スキップ")


if __name__ == "__main__":
    main()
