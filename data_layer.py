"""data_layer.py — the ONE data adapter for War Room OS.

Real data on YOUR machine (yfinance + FRED fredgraph, no API key needed), synthetic
fallback anywhere else (sandbox / offline). FAILS SOFT to synthetic and STAMPS the source
so the dashboard is always honest about whether it is showing live or synthetic data.

Per-market universes are extensible — add tickers here, they flow through the whole pipeline.
On-chain (crypto) + COT (commodity/fx) need their own feeds/keys (onchain_engine, cftc_cot_scraper);
until wired, those markets score on price + the market_drivers matrix only (flagged in the UI).
"""
from __future__ import annotations
import io, sys, time
import numpy as np
import pandas as pd

# ─────────────────────────── per-market universes (extend freely) ───────────────────────────
UNIVERSE = {
    "us": ["NVDA","AMD","AVGO","MRVL","MU","AXTI","AAOI","COHR","LITE","CRDO","ALAB","AEHR","FORM",
           "GEV","VRT","ETN","POWL","CEG","VST","CCJ","UEC","SMCI","DELL","ARM","ASML","TSM"],
    "idx": ["BBCA.JK","BREN.JK","BRMS.JK","ADRO.JK","ANTM.JK","MDKA.JK","TLKM.JK","GOTO.JK"],
    "crypto": ["BTC-USD","ETH-USD","SOL-USD","BNB-USD","LINK-USD","RENDER-USD"],
    "commodity": ["CL=F","BZ=F","GC=F","SI=F","HG=F","NG=F"],
    "fx": ["EURUSD=X","USDJPY=X","GBPUSD=X","AUDUSD=X","USDIDR=X","DX-Y.NYB"],
}
BENCH = "SPY"

# FRED series that power liquidity / macro (fredgraph CSV, no key)
FRED_SERIES = {
    "WALCL":"Fed balance sheet","RRPONTSYD":"Reverse repo","WTREGEN":"Treasury general acct",
    "DFII10":"Real 10Y (TIPS)","T10YIE":"10Y breakeven","BAMLH0A0HYM2":"HY OAS",
}


def _synth(n=500, drift=0.0004, vol=0.02, start=100.0, seed=None):
    if seed is not None:
        np.random.seed(seed)
    idx = pd.date_range(end=pd.Timestamp.today().normalize(), periods=n, freq="B")
    r = np.random.normal(drift, vol, len(idx))
    return pd.Series(start * np.exp(np.cumsum(r)), index=idx)


def load_prices(tickers, start="2022-01-01", allow_live=True):
    """Return ({ticker: close Series}, source_str). Tries yfinance; falls back to synthetic."""
    if allow_live:
        try:
            import yfinance as yf
            data = yf.download(list(tickers), start=start, auto_adjust=True,
                               progress=False, threads=True)
            close = data["Close"] if isinstance(data.columns, pd.MultiIndex) and "Close" in data.columns.get_level_values(0) else data
            out = {}
            if isinstance(close, pd.DataFrame):
                for t in close.columns:
                    s = close[t].dropna()
                    if len(s) > 200:
                        out[t] = s
            else:  # single ticker
                s = close.dropna()
                if len(s) > 200:
                    out[list(tickers)[0]] = s
            if out:
                return out, "LIVE (yfinance)"
        except ImportError:
            pass
        except Exception as e:
            sys.stderr.write(f"[data_layer] yfinance failed ({e}) → synthetic fallback\n")
    # synthetic fallback — deterministic per ticker so the dashboard is stable
    out = {}
    for i, t in enumerate(tickers):
        drift = 0.0003 + (hash(t) % 11) * 0.0001
        out[t] = _synth(drift=drift, seed=(abs(hash(t)) % 9999))
    return out, "SYNTHETIC (offline fallback)"


def load_fred(allow_live=True):
    """FRED via fredgraph CSV (no API key). Returns {series_id: Series}. Empty if offline."""
    if not allow_live:
        return {}, "OFFLINE"
    out = {}
    try:
        import urllib.request
        for sid in FRED_SERIES:
            try:
                url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"
                with urllib.request.urlopen(url, timeout=10) as r:
                    df = pd.read_csv(io.BytesIO(r.read()))
                df.columns = ["date", "value"]
                df["value"] = pd.to_numeric(df["value"], errors="coerce")
                s = df.dropna().set_index(pd.to_datetime(df["date"]))["value"]
                if len(s) > 10:
                    out[sid] = s
            except Exception:
                continue
        if out:
            return out, "LIVE (FRED fredgraph)"
    except Exception:
        pass
    return {}, "OFFLINE (no FRED — liquidity uses price proxy)"


def load_all(markets=None, start="2022-01-01", allow_live=True):
    """Delegate to YOUR loaders: warroom.data.load (cache→yfinance→synthetic) + warroom.fred.fetch
    (fredgraph, no key) + gcfis.feeds.typef_idx (IDX). Falls back to the local synthetic only if a
    loader is unavailable. On your machine these fetch REAL data; the sandbox blocks the network."""
    markets = markets or list(UNIVERSE.keys())
    prices, ohlcv, sources = {}, {}, {}
    # ---- prices via warroom.data (your loader) ----
    try:
        from warroom import data as WD
        UNI = {"us": getattr(WD, "US_UNIVERSE", UNIVERSE["us"]),
               "idx": getattr(WD, "IDX_UNIVERSE", UNIVERSE["idx"]),
               "crypto": UNIVERSE["crypto"], "commodity": UNIVERSE["commodity"], "fx": UNIVERSE["fx"]}
        for m in markets:
            px, src = WD.load(UNI.get(m, UNIVERSE.get(m, [])), days=500)
            prices[m] = px; sources[m] = f"warroom.data · {src}"
    except Exception:
        for m in markets:
            px, src = load_prices(UNIVERSE.get(m, []), start, allow_live)
            prices[m] = px; sources[m] = src
    # ---- OHLCV for the price-signal path (bandarmetrics) ----
    try:
        from data.loader import load_ohlcv
        for m in markets:
            oh = load_ohlcv(list(prices[m].keys())[:60])
            if oh: ohlcv[m] = oh
    except Exception:
        pass
    # ---- FRED via warroom.fred (your fetcher) ----
    fred, fsrc = {}, "unavailable"
    try:
        from warroom import fred as WF
        fred = WF.fetch() or {}
        fsrc = f"warroom.fred · {len(fred)} series" if fred else "warroom.fred · empty (offline)"
    except Exception as e:
        fred, fsrc = {}, f"warroom.fred failed ({e})"
    # ---- VIX (bundled) ----
    vix = None
    try:
        import os as _os
        vp = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "research", "vix.csv")
        if _os.path.exists(vp):
            v = pd.read_csv(vp); v["DATE"] = pd.to_datetime(v["DATE"]); vix = v.set_index("DATE")["CLOSE"]
    except Exception:
        pass
    benchpx, bsrc = load_prices([BENCH], start, allow_live)
    bench = prices.get("us", {}).get(BENCH) if prices.get("us", {}).get(BENCH) is not None else benchpx.get(BENCH)
    live = any("live" in str(s).lower() or "yfinance" in str(s).lower() for s in sources.values()) or ("series" in fsrc and "empty" not in fsrc)
    return {"prices": prices, "ohlcv": ohlcv, "bench": bench, "fred": fred, "vix": vix,
            "sources": sources, "bench_source": bsrc, "fred_source": fsrc,
            "overall_source": "LIVE" if live else "SYNTHETIC", "markets": markets}



if __name__ == "__main__":
    d = load_all(allow_live=True)
    print("overall source:", d["overall_source"])
    for m, src in d["sources"].items():
        print(f"  {m:10} {len(d['prices'][m]):>2} tickers  [{src}]")
    print("  bench:", d["bench_source"], "| fred:", d["fred_source"], f"({len(d['fred'])} series)")
