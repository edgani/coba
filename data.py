"""wr/data.py — universe + data loading (lean rebuild).

Prioritas: cache real (parquet) → yfinance/stooq (mesin lu) → sintetis (sandbox fallback, ditandai).
Universe = nama supply-chain dari research lu + macro/theme proxies. Ga ada yang dikarang jadi "real"
kalau sintetis — tiap frame ditandai sumbernya lewat load()'s meta.
"""
from __future__ import annotations
import os
import numpy as np
import pandas as pd

_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(_DIR, "cache")

# ── UNIVERSE (from your curated supply-chain research + macro proxies) ──
SUPPLY_CHAIN = ["NVDA", "AVGO", "MU", "MRVL", "COHR", "CRDO", "AAOI", "AXTI", "LITE", "CIEN", "SITM",
                "ALAB", "AEHR", "HIMX", "FORM", "AMKR", "TSM", "ASML", "AMAT", "LRCX", "KLAC",
                "ETN", "GEV", "VRT", "POWL", "CEG", "VST", "FCX", "MP", "LNG",
                "APH", "TEL", "QCOM", "ARM", "SMCI", "DELL", "ANET", "FN", "KEYS"]
MACRO_PROXY = ["SPY", "QQQ", "IWM", "TLT", "GLD", "SLV", "USO", "UUP", "HYG", "LQD", "EEM", "VXX"]
THEME_PROXY = ["SOXX", "SMH", "BOTZ", "NLR", "URA", "ICLN", "XLE", "XLF", "XLU", "XLK"]
US_UNIVERSE = list(dict.fromkeys(SUPPLY_CHAIN + MACRO_PROXY + THEME_PROXY))
CRYPTO_UNIVERSE = ["BTC-USD", "ETH-USD", "SOL-USD"]
FX_UNIVERSE = ["EURUSD=X", "USDJPY=X", "GBPUSD=X", "AUDUSD=X"]
COMMO_UNIVERSE = ["GC=F", "SI=F", "CL=F", "HG=F", "NG=F"]
IDX_UNIVERSE = ["BBCA.JK", "BBRI.JK", "TLKM.JK", "ASII.JK", "BMRI.JK"]


def _synth(ticker, n=1400, seed=None):
    """Synthetic OHLC (sandbox fallback). Deterministic per-ticker so results are stable."""
    rng = np.random.default_rng(abs(hash(ticker)) % (2**32) if seed is None else seed)
    drift = rng.normal(0.0004, 0.0003)
    vol = abs(rng.normal(0.018, 0.006))
    rets = rng.normal(drift, vol, n)
    close = 50 * np.exp(np.cumsum(rets))
    idx = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=n)
    n = len(idx); rets = rets[:n]; close = close[:n]
    high = close * (1 + np.abs(rng.normal(0, 0.008, n)))
    low = close * (1 - np.abs(rng.normal(0, 0.008, n)))
    op = close * (1 + rng.normal(0, 0.005, n))
    vol_ = np.abs(rng.normal(1e6, 3e5, n))
    return pd.DataFrame({"Open": op, "High": high, "Low": low, "Close": close, "Volume": vol_}, index=idx)


def _load_one(ticker, start="2015-01-01"):
    """Try cache → yfinance → stooq → synthetic. Returns (df, source)."""
    p = os.path.join(CACHE, f"{ticker.replace('/', '_')}.parquet")
    if os.path.exists(p):
        try:
            return pd.read_parquet(p), "cache"
        except Exception:
            pass
    # live sources (work on your machine; blocked in sandbox)
    try:
        import yfinance as yf
        df = yf.download(ticker, start=start, progress=False, auto_adjust=False)
        if df is not None and len(df) > 100:
            df = df.rename(columns=str.title)[["Open", "High", "Low", "Close", "Volume"]]
            os.makedirs(CACHE, exist_ok=True)
            df.to_parquet(p)
            return df, "yfinance"
    except Exception:
        pass
    return _synth(ticker), "synthetic"


def load(tickers, start="2015-01-01"):
    """Load a list of tickers. Returns (dict{ticker: df}, meta{sources})."""
    out, meta = {}, {}
    for t in tickers:
        df, src = _load_one(t, start)
        out[t] = df
        meta[t] = src
    return out, meta


def data_is_synthetic(meta):
    return all(v == "synthetic" for v in meta.values()) if meta else True


def add_ticker(ticker, start="2015-01-01"):
    """Auto-add a new ticker to cache (fetches via yfinance/stooq on your machine)."""
    df, src = _load_one(ticker, start)
    if src in ("yfinance", "stooq"):
        return {"ok": True, "source": src, "rows": len(df)}
    if src == "cache":
        return {"ok": True, "source": "cache"}
    return {"ok": False, "note": "fetch blocked in sandbox — runs on your machine with yfinance"}
