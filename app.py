"""app.py — War Room OS · renders the APPROVED v0.3 dashboard design.

    streamlit run app.py

Serves the dashboard you approved (dashboard.html) — the dense terminal with Mission Control,
per-market setup cards, asymmetric alpha cards, and the traceback spine. Three data modes:
  • Demo (approved design)   — the illustrative mock exactly as approved (default; always looks right)
  • Real S&P history         — runs the engines on the bundled 2013-2018 panel → REAL US tickers
  • Live (your feeds)        — yfinance + FRED on your machine → real, current, cross-market
Empty setups on thin data are correct (the gate refuses to fabricate). The design never degrades.
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
    """Build the data_layer dict from the REAL bundled S&P panel (US market)."""
    import pandas as pd
    p = pd.read_parquet(os.path.join(HERE, "research", "sp500_panel.parquet"))
    p["date"] = pd.to_datetime(p["date"])
    close = p.pivot_table(index="date", columns="Name", values="close").sort_index()
    close = close[close.columns[close.notna().mean() > 0.9]]
    prices = {t: close[t].dropna() for t in close.columns}
    return {"prices": {"us": prices}, "bench": close.mean(axis=1), "markets": ["us"],
            "sources": {"us": "REAL S&P panel 2013-2018"}, "bench_source": "panel",
            "fred_source": "none", "overall_source": "REAL-HISTORICAL"}


@st.cache_data(ttl=1800, show_spinner="Running the engines…")
def _run(mode, markets):
    from run import build_desk
    if mode == "panel":
        return build_desk(_panel_data())
    import data_layer as DL
    data = DL.load_all(markets=list(markets), allow_live=(mode == "live"))
    return build_desk(data)


with st.sidebar:
    st.markdown("**War Room OS**")
    mode = st.radio("Data source", [
        "Demo (approved design)", "Real S&P history (2013-18)", "Live (your feeds)"],
        help="Demo = the illustrative mock you approved. The other two run the real engines.")
    mkts = st.multiselect("Markets (live)", ["us", "idx", "crypto", "commodity", "fx"],
                          default=["us", "crypto", "commodity", "fx"])
    st.caption("The design is fixed (your v0.3). Only the data changes — always labeled.")

if mode.startswith("Demo"):
    html = open(DASH_PATH, encoding="utf-8").read()
else:
    try:
        desk = _run("panel" if mode.startswith("Real") else "live", tuple(mkts))
        html = _inject(desk)
        n_set = sum(len(m["setups"]) for m in desk["markets"].values())
        st.toast(f"{desk['meta']['source']} · universe {desk['meta']['universe_n']} · {n_set} setups")
    except Exception as e:
        st.warning(f"data unavailable ({e}) — showing the approved demo instead.")
        html = open(DASH_PATH, encoding="utf-8").read()

components.html(html, height=1150, scrolling=True)
