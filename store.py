"""配信データを SQLite に蓄積する共通モジュール"""

import sqlite3
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))
DB_PATH = "alerts.db"


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def save_portfolio(stocks: list[dict], session: str):
    ts = datetime.now(JST).isoformat()
    conn = _conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS portfolio (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            ts         TEXT NOT NULL,
            session    TEXT NOT NULL,
            code       TEXT NOT NULL,
            shares     INTEGER NOT NULL,
            price      REAL NOT NULL,
            value      REAL NOT NULL,
            change_pct REAL NOT NULL
        )
    """)
    conn.executemany(
        "INSERT INTO portfolio (ts, session, code, shares, price, value, change_pct) VALUES (?,?,?,?,?,?,?)",
        [(ts, session, s["code"], s["shares"], s["price"], s["value"], s["change_pct"]) for s in stocks],
    )
    conn.commit()
    conn.close()


def save_lowcheck(stocks: list[dict]):
    ts = datetime.now(JST).isoformat()
    conn = _conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS lowcheck (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            ts      TEXT NOT NULL,
            code    TEXT NOT NULL,
            name    TEXT NOT NULL,
            price   REAL NOT NULL,
            low_26w REAL NOT NULL,
            pct_26w REAL NOT NULL,
            low_52w REAL NOT NULL,
            pct_52w REAL NOT NULL
        )
    """)
    conn.executemany(
        "INSERT INTO lowcheck (ts, code, name, price, low_26w, pct_26w, low_52w, pct_52w) VALUES (?,?,?,?,?,?,?,?)",
        [
            (ts, s["code"], s["name"], s["price"],
             s["lows"]["26w"]["low"], s["lows"]["26w"]["pct"],
             s["lows"]["52w"]["low"], s["lows"]["52w"]["pct"])
            for s in stocks
        ],
    )
    conn.commit()
    conn.close()


def save_dividend(stocks: list[dict]):
    ts = datetime.now(JST).isoformat()
    conn = _conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS dividend (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            ts              TEXT NOT NULL,
            code            TEXT NOT NULL,
            name            TEXT NOT NULL,
            sector          TEXT NOT NULL,
            price           REAL NOT NULL,
            dividend_yield  REAL NOT NULL,
            annual_dividend REAL NOT NULL
        )
    """)
    conn.executemany(
        "INSERT INTO dividend (ts, code, name, sector, price, dividend_yield, annual_dividend) VALUES (?,?,?,?,?,?,?)",
        [
            (ts, s["ticker"].replace(".T", ""), s["name"], s.get("sector", ""),
             s["price"], s["dividend_yield"], s["annual_dividend"])
            for s in stocks
        ],
    )
    conn.commit()
    conn.close()
