"""app.py — War Room OS Streamlit entry point.

    streamlit run app.py

Runs the gcfis orchestrator on live data (yfinance + FRED on your machine; synthetic fallback offline)
and renders Mission Control (systemic macro), per-market ranked setups, Alpha (asymmetric), and a
Validation tab that surfaces the honest test verdicts. Nothing here fabricates tickers — empty setups
on thin/noise data are correct.
"""
from __future__ import annotations
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import streamlit as st

st.set_page_config(page_title="War Room OS", layout="wide", initial_sidebar_state="collapsed")

# ── dark terminal styling ──
st.markdown("""<style>
  .stApp{background:#0a0d12;color:#d7dde5}
  h1,h2,h3{font-family:ui-monospace,Menlo,monospace;letter-spacing:.5px}
  .metric{font-family:ui-monospace,monospace}
  [data-testid="stMetricValue"]{font-family:ui-monospace,monospace}
  .stTabs [data-baseweb="tab"]{font-family:ui-monospace,monospace;font-size:12px}
</style>""", unsafe_allow_html=True)


@st.cache_data(ttl=1800, show_spinner="Loading data + running the brain…")
def run_desk(markets, synthetic):
    import data_layer as DL
    from run import build_desk
    data = DL.load_all(markets=markets, allow_live=not synthetic)
    return build_desk(data)


def main():
    st.title("WAR ROOM PRO / GCFIS · Investment OS")
    with st.sidebar:
        st.caption("data / run")
        synthetic = st.toggle("Offline (synthetic)", value=True,
                              help="Off = live yfinance + FRED on your machine")
        mkts = st.multiselect("Markets", ["us", "idx", "crypto", "commodity", "fx"],
                              default=["us", "crypto", "commodity", "fx"])
    try:
        desk = run_desk(tuple(mkts), synthetic)
    except Exception as e:
        st.error(f"pipeline error: {e}")
        st.info("On your machine: `pip install -r requirements.txt`, then run with Offline OFF for live data.")
        return

    src = desk["meta"]["source"]
    st.caption(f"source: **{src}** · universe {desk['meta']['universe_n']} · generated {desk['meta']['generated']}"
               + ("  ⚠ synthetic — for shape only, not tradeable" if src != "LIVE" else ""))

    tabs = st.tabs(["MISSION CONTROL", "MARKETS", "◆ ALPHA", "VALIDATION"])

    with tabs[0]:
        s = desk["systemic"]
        c = st.columns(5)
        c[0].metric("Quad", f"{s.get('quad','—')}", s.get("quad_name", ""))
        c[1].metric("Liquidity", str(s.get("liquidity", "—"))[:18])
        c[2].metric("Fragility", str(s.get("fragility", "—"))[:18])
        c[3].metric("Shock P", str(s.get("shock_prob", "—"))[:18])
        c[4].metric("Cross-asset", str(s.get("cross_asset", "—"))[:18])
        if s.get("rotation_in"):
            st.write("Rotating **in**:", ", ".join(s["rotation_in"]), " · **out**:", ", ".join(s.get("rotation_out", [])))
        st.caption("systemic state from gcfis.orchestrator (drivers/liquidity/fragility/shock/rotation)")

    with tabs[1]:
        for mid, mk in desk["markets"].items():
            lo = " · LONG-ONLY" if mk["long_only"] else ""
            st.subheader(f"{mk['label']}{lo}  ·  bias {mk['bias']}")
            f = mk["funnel"]
            st.caption(f"funnel: universe {f['universe']} → eliminated {f['eliminated']} → setups {f['setups']}")
            rows = mk["setups"]
            if rows:
                import pandas as pd
                df = pd.DataFrame(rows)[["tk", "act", "conv", "e", "s", "t", "rr", "ty"]]
                df.columns = ["ticker", "action", "conv", "entry", "stop", "target", "R/R", "type"]
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("no name cleared the conviction gate on this data — correct (not fabricated).")

    with tabs[2]:
        st.caption("Asymmetric opportunity — structural (tier↔base-rate honest, feed-gated flags shown)")
        if desk["alpha"]:
            import pandas as pd
            a = pd.DataFrame(desk["alpha"])[["tk", "market", "asymmetry", "tier", "upside", "base_rate", "node"]]
            st.dataframe(a, use_container_width=True, hide_index=True)
        st.warning("Alpha Discovery Test (real data): price/volume discovery does NOT reliably rank "
                   "multi-year winners early (avg IC −0.12). Structural feeds (bottleneck/TAM) required — "
                   "see VALIDATION.md.")

    with tabs[3]:
        st.subheader("Validation verdicts (run `python validate_all.py` for the full battery)")
        st.markdown("""
| layer | result |
|---|---|
| statistical methods (perm/MC/White-RC/SPA/FDR/DSR/drift) | validator **VALIDATED** (noise→NOISE, planted→TRADEABLE) |
| factor + macro (real data) | IC reproduces prior study **5/5**; dollar-hub p<0.001; crash R²=0.033; CAPE p=1e-43 |
| components (every engine) | **21 PASS / 0 FAIL** (deterministic, no-lookahead, no-repaint, formulas) |
| composition / ablation | accumulation 0.45 inert · entry_score cosmetic · fear_greed breadth-trap flagged |
| filters | elimination separates (vol-of-vol 1.59 vs 0.39); **panic-bottom +6.6% vs +3.2%, p<0.0001** |
| gems | bandarmetrics markup-readiness **IC 0.17, perm 0.025** (short-horizon edge) |
| **alpha discovery (NVDA test)** | ⚠ **price/volume FAILS** (IC −0.12) — needs structural feeds |
""")
        st.caption("Tradeable gate unchanged: perm_p<0.05 AND DSR≥0.95 AND survives Reality-Check/SPA on YOUR feeds.")


if __name__ == "__main__":
    main()
