"""JPX上場銘柄リスト取得"""

import io
import logging

import pandas as pd
import requests

logger = logging.getLogger(__name__)

JPX_URL = "https://www.jpx.co.jp/markets/statistics-equities/misc/tvdivq0000001vg2-att/data_j.xls"

# プライム/スタンダード/グロース市場の内国株式のみ対象
TARGET_MARKETS = {
    "プライム（内国株式）",
    "スタンダード（内国株式）",
    "グロース（内国株式）",
}


def fetch_tse_tickers() -> list[dict]:
    """JPX公開Excelから東証上場銘柄リストを取得する。

    Returns:
        list[dict]: 各銘柄の情報 {"ticker": "7203.T", "name": "トヨタ自動車", "sector": "輸送用機器"}
    """
    logger.info("JPX銘柄リストをダウンロード中...")
    resp = requests.get(JPX_URL, timeout=60, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()

    df = pd.read_excel(io.BytesIO(resp.content), header=0)
    logger.info(f"JPXリスト取得完了: {len(df)}行")

    # 市場フィルタ
    mask = df["市場・商品区分"].isin(TARGET_MARKETS)
    filtered = df[mask].copy()
    logger.info(f"内国株式フィルタ後: {len(filtered)}銘柄")

    results = []
    for _, row in filtered.iterrows():
        code = str(row["コード"]).strip()
        results.append({
            "ticker": f"{code}.T",
            "name": str(row.get("銘柄名", "")),
            "sector": str(row.get("33業種区分", "")),
        })

    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    tickers = fetch_tse_tickers()
    print(f"取得銘柄数: {len(tickers)}")
    for t in tickers[:10]:
        print(f"  {t['ticker']} {t['name']} ({t['sector']})")
