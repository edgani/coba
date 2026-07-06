"""app.py — War Room OS · renders the APPROVED v0.3 dashboard design.

    streamlit run app.py

Serves the dashboard you approved (dashboard.html). Data modes:
  • Real S&P history (default) — engines on the bundled 2013-18 panel + real macro → REAL US tickers
  • Live (your feeds)          — warroom.data + warroom.fred on your machine → real, current, cross-market
  • Demo (approved design)     — the illustrative mock, exactly as approved
The design never degrades; only the data does, and the badge always says which.
"""
from __future__ import annotations
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="War Room OS", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""<style>
  .stApp{background:#0a0d12}
  header[data-testid="stHeader"]{background:transparent}
  .block-container{padding:0 !important;max-width:100% !important}
  #MainMenu,footer{visibility:hidden}
</style>""", unsafe_allow_html=True)

DASH_PATH = os.path.join(HERE, "dashboard.html")


def _inject(desk):
    html = open(DASH_PATH, encoding="utf-8").read()
    payload = "window.DASHBOARD_DATA = " + json.dumps(desk, default=str) + ";"
    if "/*__INJECT_DATA__*/" in html:
        return html.replace("/*__INJECT_DATA__*/", payload)
    return html.replace("<body>", "<body>\n<script>" + payload + "</script>", 1)


def _panel_data():
    """REAL bundled data: US prices + OHLCV + real macro (rate10/gold/oil/dxy) + VIX. No synthetic Fed."""
    import pandas as pd
    RES = os.path.join(HERE, "research")
    p = pd.read_parquet(os.path.join(RES, "sp500_panel.parquet")); p["date"] = pd.to_datetime(p["date"])
    piv = lambda c: p.pivot_table(index="date", columns="Name", values=c).sort_index()
    close, vol, hi, lo, op = piv("close"), piv("volume"), piv("high"), piv("low"), piv("open")
    keep = close.columns[close.notna().mean() > 0.9]; close = close[keep]
    prices = {t: close[t].dropna() for t in keep}
    ohlcv = {t: pd.DataFrame({"Open": op[t], "High": hi[t], "Low": lo[t], "Close": close[t], "Volume": vol[t]}) for t in keep}
    fred, vix = {}, None
    try:
        mp = pd.read_parquet(os.path.join(RES, "macro_panel.parquet"))
        if "rate10" in mp.columns: fred["DGS10"] = mp["rate10"].dropna()
        for col, tk in [("gold", "GC=F"), ("oil", "CL=F"), ("dxy", "DX-Y.NYB")]:
            if col in mp.columns: prices[tk] = mp[col].dropna()
    except Exception: pass
    try:
        v = pd.read_csv(os.path.join(RES, "vix.csv")); v["DATE"] = pd.to_datetime(v["DATE"])
        vix = v.set_index("DATE")["CLOSE"]
    except Exception: pass
    return {"prices": {"us": prices}, "ohlcv": {"us": ohlcv}, "bench": close.mean(axis=1),
            "markets": ["us"], "fred": fred, "vix": vix, "sources": {"us": "REAL S&P panel 2013-2018"},
            "bench_source": "panel", "fred_source": "real macro (panel); FRED liquidity = Live mode",
            "overall_source": "REAL-HISTORICAL"}


@st.cache_data(ttl=1800, show_spinner="Running the engines on real data…")
def _run(mode, markets):
    from run import build_desk
    if mode == "panel":
        return build_desk(_panel_data())
    import data_layer as DL
    data = DL.load_all(markets=list(markets), allow_live=(mode == "live"))
    return build_desk(data)


with st.sidebar:
    st.markdown("**War Room OS**")
    _cache = os.path.join(HERE, "cache", "prices.parquet")
    _has_cache = os.path.exists(_cache)
    _opts = ["Live (your feeds)", "Real S&P history (2013-18)", "Demo (approved design)"] if _has_cache \
        else ["Real S&P history (2013-18)", "Live (your feeds)", "Demo (approved design)"]
    mode = st.radio("Data source", _opts,
        help="Live reads cache/prices.parquet (real current prices) if you built it; else falls back.")
    mkts = st.multiselect("Markets (live)", ["us", "idx", "crypto", "commodity", "fx"],
                          default=["us", "crypto", "commodity", "fx"])
    st.caption("Design is fixed (your v0.3). Only the data changes — badge shows which.")

# ── unambiguous data-source status (so you SEE whether real data loaded) ──
_cache = os.path.join(HERE, "cache", "prices.parquet")
if os.path.exists(_cache):
    try:
        import pandas as _pd
        _df = _pd.read_parquet(_cache)
        _n = _df.columns.get_level_values(0).nunique() if hasattr(_df.columns, "get_level_values") else len(_df.columns)
        st.success(f"✓ Local price cache found — {_n} tickers, latest {str(_df.index.max())[:10]}. "
                   f"Live mode uses REAL current prices.")
    except Exception:
        st.info("Local cache present but unreadable — rebuild with `python build_cache.py --full`.")
else:
    st.warning("⚠ No local price cache → Live mode can't show current prices (Yahoo rate-limits cloud IPs). "
               "Run `python build_cache.py --full` locally, commit cache/prices.parquet, redeploy. "
               "Meanwhile 'Real S&P history' shows REAL 2013-18 data (NVDA≈182 = its real 2018 price, not today's).")

if mode.startswith("Demo"):
    html = open(DASH_PATH, encoding="utf-8").read()
else:
    try:
        desk = _run("panel" if mode.startswith("Real") else "live", tuple(mkts))
        html = _inject(desk)
        n = sum(len(m["setups"]) for m in desk["markets"].values())
        st.toast(f"{desk['meta']['source']} · universe {desk['meta']['universe_n']} · {n} setups")
    except Exception as e:
        st.warning(f"data unavailable ({e}) — showing the approved demo instead.")
        html = open(DASH_PATH, encoding="utf-8").read()

components.html(html, height=1150, scrolling=True)
