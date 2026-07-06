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
    """Load every market + bench + FRED. Returns a dict the runner consumes."""
    markets = markets or list(UNIVERSE.keys())
    prices, sources = {}, {}
    for m in markets:
        px, src = load_prices(UNIVERSE[m], start, allow_live)
        prices[m] = px
        sources[m] = src
    benchpx, bsrc = load_prices([BENCH], start, allow_live)
    bench = benchpx.get(BENCH)
    fred, fsrc = load_fred(allow_live)
    live = any("LIVE" in s for s in sources.values())
    overall = "LIVE" if live else "SYNTHETIC"
    return {"prices": prices, "bench": bench, "fred": fred,
            "sources": sources, "bench_source": bsrc, "fred_source": fsrc,
            "overall_source": overall, "markets": markets}


if __name__ == "__main__":
    d = load_all(allow_live=True)
    print("overall source:", d["overall_source"])
    for m, src in d["sources"].items():
        print(f"  {m:10} {len(d['prices'][m]):>2} tickers  [{src}]")
    print("  bench:", d["bench_source"], "| fred:", d["fred_source"], f"({len(d['fred'])} series)")
