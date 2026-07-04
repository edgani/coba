"""
War Room — entry point.  Run:  streamlit run app.py

Architecture:
  • Design + ranking  = mine (warroom/render.py, warroom/compute.py) — verdict-first mockup.
  • Formula engines   = your zip (engines/, gcfis/) called as providers: Hedgeye GIP (structural+
    monthly), Hedgeye Risk Range, GEX/greeks, methodology (Citrini/Yves/Soros/Coatue/Druck via
    thought_process), lead-lag (Granger+TE) + supply-chain-graph for propagation, value-based LPM.
  • NO old UI, NO old ticker-filter/elimination pipeline.
Data: parquet cache (build_cache.py) → yfinance live → synthetic fallback. FRED via fredgraph (no key).
"""
import streamlit as st
from warroom import data as D, compute as C, render as R, fred as F, feeds as FEEDS, tracker as TR, statelog as SL
from warroom import brief_export as BE


def main():
    st.set_page_config(page_title="War Room", layout="wide", initial_sidebar_state="collapsed")
    with st.spinner("Loading prices + running engines…"):
        us, source = D.load(D.US_UNIVERSE)
        idx, _ = D.load(D.IDX_UNIVERSE)
        cp, _ = D.load(D.CRYPTO_UNIVERSE)
        fxp, _ = D.load(D.FX_UNIVERSE)
        commo, _ = D.load(D.COMMO_UNIVERSE)
        feeds = FEEDS.load_feeds()                     # live-feed snapshot (build_feeds.py); empty = proxy
        fred = feeds.get("fred") or F.fetch()
        d = C.run(us, idx, cp, fxp, commo, fred, feeds)
        # forward-test logger: log today's conviction point-in-time, then resolve open signals on later bars
        allpx = {**commo, **fxp, **cp, **idx, **us}
        try:
            TR.log_signals(d["conviction"], d["regime"])
            TR.update_outcomes(allpx)
        except Exception:
            pass
        try:
            d["whatchanged"], d["whatchanged_prev_ts"] = SL.record_and_diff(d)
        except Exception:
            d["whatchanged"], d["whatchanged_prev_ts"] = [], None
        try:
            BE.export(d)   # regenerate the interactive briefing deck (briefing.html) with today's data
        except Exception:
            pass
    # Redesigned: 13 logically-grouped tabs (correlated things together, not scattered).
    tabs = st.tabs(["Mission Control", "Macro & Regime", "Early Warning", "Alpha & Tickers",
                    "Crypto", "Commodities", "FX", "IHSG",
                    "Flow & Rotation", "Knowledge Graph", "Validation", "Brief", "Portfolio"])
    with tabs[0]:                       # HUB: today's attention, meters, top signals
        R.mission_control(d)
    with tabs[1]:                       # MACRO cluster: cross-asset playbook + regime state + decision engine
        R.cross_asset_macro(d)
        R.market_state(d)
        R.command_center(d, source)
    with tabs[2]:                       # RISK timing: panic/fear-greed/crash-lead/valuation
        R.early_warning_tab(d)
    with tabs[3]:                       # ALPHA: where the tickers come out — ranking + decision market + US names + fair value
        R.alpha(d)
        R.us_stocks(d)
        R.fair_value_cards(d)
    with tabs[4]: R.crypto(d)           # per-market DNA (blueprint keeps these distinct)
    with tabs[5]: R.commodities(d)
    with tabs[6]: R.fx(d)
    with tabs[7]: R.ihsg(d)
    with tabs[8]:                       # FLOW cluster: rotation map + ETF/sector flow
        R.cycle_rotation(d)
        R.flow(d)
    with tabs[9]:                       # KNOWLEDGE GRAPH cluster: connected network + chains + company cards
        R.knowledge_graph_view(d)
        R.causal_chains(d)
        R.knowledge_cards(d)
        R.theme_library(d)
        R.catalyst_timeline(d)
        R.bottleneck(d)
        R.node_template(d)
    with tabs[10]:                      # META: signal confidence / certification
        R.validation_tab(d)
    with tabs[11]:                      # BRIEF cluster: morning brief + reasoning narrative
        R.morning_brief(d)
        R.briefing_embed()
    with tabs[12]:                      # PORTFOLIO cluster: track record + decision journal + risk & health
        R.track_record(TR.performance(), TR.open_positions(), TR.closed_trades())
        R.decision_journal_tab(d)
        R.risk_health(d)


if __name__ == "__main__":
    main()
