"""全角幅考慮のテキストユーティリティ"""

import unicodedata


def width(s: str) -> int:
    """全角2, 半角1で文字幅を計算"""
    return sum(2 if unicodedata.east_asian_width(c) in ("F", "W") else 1 for c in s)


def pad(s: str, w: int) -> str:
    """全角考慮で右パディング"""
    return s + " " * (w - width(s))


def trunc(s: str, w: int) -> str:
    """全角考慮で切り詰め"""
    cur = 0
    for i, c in enumerate(s):
        cw = 2 if unicodedata.east_asian_width(c) in ("F", "W") else 1
        if cur + cw > w:
            return s[:i]
        cur += cw
    return s


def fit(s: str, w: int) -> str:
    """切り詰め+パディングで固定幅に"""
    return pad(trunc(s, w), w)
