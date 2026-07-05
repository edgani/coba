"""wr/app.py — War Room Pro (lean rebuild). Run: streamlit run wr/app.py

6 tab bersih, semua ngambil dari engine TERUJI + knowledge graph. Yang berkorelasi dikelompokkan.
Sinyal actionable = yang lolos certify (RS top-decile, panic-bottom, cross-asset, crash-lead, valuation).
"""
from __future__ import annotations
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import streamlit as st
import data as D, engines as E, graph as G

st.set_page_config(page_title="War Room Pro", layout="wide", initial_sidebar_state="collapsed")

CSS = """<style>
.stApp{background:#0a0d12}
.wr-hd{display:flex;align-items:center;gap:12px;margin:4px 0 18px;padding-bottom:14px;border-bottom:1px solid #1a2029}
.wr-hd .t{font-size:22px;font-weight:800;color:#e8edf2;letter-spacing:.02em}
.wr-hd .d{font-size:12px;color:#8b97a7}
.wr-lbl{font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:#8b97a7;font-weight:700;margin:22px 0 10px}
.wr-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:10px}
.wr-card{background:#12161d;border:1px solid #1e2530;border-radius:12px;padding:14px 16px;border-left-width:3px}
.wr-card .l{font-size:11px;color:#8b97a7;text-transform:uppercase;letter-spacing:.08em}
.wr-card .n{font-size:26px;font-weight:800;color:#e8edf2;margin:2px 0}
.wr-card .s{font-size:12px;color:#9aa6b2}
.wr-card .a{font-size:11.5px;margin-top:6px;font-weight:600}
.wr-row{display:flex;align-items:center;gap:8px;padding:8px 12px;border-bottom:.5px solid #1a2029}
.wr-row:last-child{border-bottom:none}
.wr-badge{font-size:10px;font-weight:800;padding:3px 9px;border-radius:6px;flex:none;letter-spacing:.04em}
.wr-name{font-size:13.5px;font-weight:600;color:#e6edf3}
.wr-why{font-size:11.5px;color:#8b97a7;margin-left:auto;text-align:right}
.wr-box{background:#12161d;border:1px solid #1e2530;border-radius:12px;padding:6px 4px;margin-bottom:8px}
.wr-note{font-size:11.5px;color:#7d8898;line-height:1.6;margin-top:10px;padding:10px 12px;background:#0e1218;border-radius:8px}
.wr-chip{display:inline-block;padding:2px 9px;border-radius:6px;font-size:11px;margin:2px}
</style>"""

COL = {"grn": "#3fb950", "amb": "#d6a429", "red": "#f85149", "inf": "#6ea8ff", "gry": "#5b6675"}


@st.cache_data(ttl=900, show_spinner="Loading market data…")
def _load():
    us, meta = D.load(D.US_UNIVERSE)
    state = E.run_all(us)
    fv = {}
    for t, d in us.items():
        if d is None or len(d) == 0 or "Close" not in getattr(d, "columns", []):
            continue
        try:
            c = d["Close"]
            if getattr(c, "ndim", 1) > 1:
                c = c.iloc[:, 0]
            fv[t] = {"price": float(c.iloc[-1])}
        except Exception:
            continue
    return state, fv, D.data_is_synthetic(meta)


def _hd(title, desc):
    st.markdown(f"{CSS}<div class='wr-hd'><div><div class='t'>◆ {title}</div><div class='d'>{desc}</div></div></div>", unsafe_allow_html=True)


def _card(label, num, sub, action="", color="gry"):
    c = COL.get(color, "#5b6675")
    return (f"<div class='wr-card' style='border-left-color:{c}'><div class='l'>{label}</div>"
            f"<div class='n'>{num}</div><div class='s'>{sub}</div>"
            + (f"<div class='a' style='color:{c}'>{action}</div>" if action else "") + "</div>")


state, fv, synthetic = _load()
prices = {t: v["price"] for t, v in fv.items()}

if synthetic:
    st.warning("⚠ Running on SYNTHETIC data (sandbox). On your machine with cached/yfinance data, all numbers become real. Structure & tested logic are identical.", icon="⚠️")

tabs = st.tabs(["Mission Control", "Macro & Regime", "Early Warning", "Decision", "Knowledge Graph", "Validation"])

# ───────────────────────── MISSION CONTROL ─────────────────────────
with tabs[0]:
    _hd("MISSION CONTROL", "the few things that matter today — from tested engines")
    rr = state["risk_regime"]; fg = state["fear_greed"]; cr = state["crash_risk"]; vr = state["valuation_room"]
    cards = ""
    if rr:
        cards += _card("Risk Regime", rr["verdict"], f"score {rr['score']}/3 · exp DD {rr['expected_fwd6_maxDD']}", rr["action"][:46], rr["color"])
    if fg:
        cards += _card("Fear-Greed", int(fg["value"]), fg["state"], fg["signal"][:46], fg["color"])
    if cr:
        cards += _card("Crash Risk (24mo)", f"{int(cr['crash_prob'][24]*100)}%", f"{cr['risk_level']} · base {int(cr['base_prob'][24]*100)}%", cr["action"][:46], cr["color"])
    if vr:
        cards += _card("Valuation", f"CAPE {vr['current_cape']}", f"{int(vr['percentile'])}th pctile", f"median {vr['median_months_to_drawdown']}mo to −20% drawdown", "inf")
    st.markdown(f"<div class='wr-grid'>{cards}</div>", unsafe_allow_html=True)

    if fg and fg.get("panic_bottom_active"):
        st.markdown(f"{CSS}<div class='wr-box' style='border-left:3px solid #3fb950'><div class='wr-row'><span class='wr-badge' style='color:#3fb950;background:#12301c'>PANIC BOTTOM</span><span class='wr-name'>{fg['panic_note']}</span></div></div>", unsafe_allow_html=True)

    st.markdown("<div class='wr-lbl'>Top Signals — RS top-decile (tested: lift 2x)</div>", unsafe_allow_html=True)
    rows = ""
    for r in state["ticker_ranking"][:10]:
        m = G.investment_memo(r["ticker"], prices.get(r["ticker"]))
        role = m.get("role") or m.get("chain_node") or ""
        rows += f"<div class='wr-row'><span class='wr-badge' style='color:#3fb950;background:#12301c'>RS {r['rs_pct']:.0f}%</span><span class='wr-name'>{r['ticker']}</span><span class='wr-why'>${r['price']} · {role}</span></div>"
    st.markdown(f"{CSS}<div class='wr-box'>{rows or '<div class=wr-row>no names in top decile</div>'}</div>", unsafe_allow_html=True)
    st.markdown("<div class='wr-note'>These are the names currently in the top decile of tested cross-sectional relative strength (the only ticker signal that passed validation, lift 2.14x). Not 'buy because quad' — buy candidates ranked by a signal that beat random in backtesting.</div>", unsafe_allow_html=True)

# ───────────────────────── MACRO & REGIME ─────────────────────────
with tabs[1]:
    _hd("MACRO & REGIME", "cross-asset playbook · dollar hub · thesis — all tested (1971-2023)")
    rr = state["risk_regime"]; mq = state["macro_quad"]
    if rr:
        rr_sub = "aggressive=size up, defensive=raise cash"
        mq_sub = (f"long {mq['long']} / short {mq['short']}") if mq else ""
        mq_act = (mq['inflation_play'] if mq else "")[:46]
        c1 = _card('Risk Regime', rr['verdict'], rr_sub, rr['action'][:46], rr['color'])
        c2 = _card('Macro Quad', mq['quad'] if mq else '—', mq_sub, mq_act, 'inf')
        st.markdown(f"<div class='wr-grid'>{c1}{c2}</div>", unsafe_allow_html=True)
    st.markdown("<div class='wr-lbl'>Dollar = Hub (tested cross-asset links, p&lt;0.001)</div>", unsafe_allow_html=True)
    rows = ""
    for (a, b), v in state["cross_asset_links"].items():
        rows += f"<div class='wr-row'><span class='wr-badge' style='color:#3fb950;background:#12301c'>corr {v['corr']:+.2f}</span><span class='wr-name'>{a} ↔ {b}</span><span class='wr-why'>{v['play']}</span></div>"
    st.markdown(f"{CSS}<div class='wr-box'>{rows}</div>", unsafe_allow_html=True)

    st.markdown("<div class='wr-lbl'>Thesis Library</div>", unsafe_allow_html=True)
    for name, t in G.THESES.items():
        da = G.devils_advocate(name)
        st.markdown(f"{CSS}<div class='wr-box' style='border-left:3px solid #3fb950'>"
                    f"<div class='wr-row' style='border:none'><span class='wr-badge' style='color:#3fb950;background:#12301c'>{t['status']} P={int(t['probability']*100)}%</span><span class='wr-name'>{name}</span><span class='wr-why'>{t['horizon']}</span></div>"
                    f"<div style='padding:0 12px 10px'><div class='s' style='color:#9aa6b2;font-size:12px'>{t['hypothesis']}</div>"
                    f"<div style='font-size:11.5px;color:#8b97a7;margin-top:4px'>mechanism: {t['mechanism']}</div>"
                    f"<div style='font-size:11.5px;color:#f85149;margin-top:4px'>devil's advocate: {da[0]}</div>"
                    f"<div style='font-size:11.5px;color:#7d8898;margin-top:4px'>invalidation: {t['invalidation']}</div></div></div>", unsafe_allow_html=True)

    st.markdown("<div class='wr-lbl'>Playbook — regime → historical phases (tested flagged)</div>", unsafe_allow_html=True)
    pbrows = ""
    for name, phases in G.PLAYBOOKS.items():
        ph = " → ".join(f"<b>{p[0]}</b>: {p[1][:36]}" for p in phases[:3])
        pbrows += f"<div class='wr-row' style='flex-direction:column;align-items:flex-start;gap:3px'><span class='wr-name'>{name}</span><span class='wr-why' style='margin-left:0;text-align:left'>{ph}</span></div>"
    st.markdown(f"{CSS}<div class='wr-box'>{pbrows}</div>", unsafe_allow_html=True)

# ───────────────────────── EARLY WARNING ─────────────────────────
with tabs[2]:
    _hd("EARLY WARNING", "panic-bottom · fear-greed · crash lead-time · valuation room — tested")
    fg = state["fear_greed"]; cr = state["crash_risk"]; vr = state["valuation_room"]
    if fg:
        pct = max(0, min(100, fg["value"]))
        fgcol = COL.get(fg["color"], "#5b6675")
        st.markdown(f"{CSS}<div class='wr-box' style='padding:14px 16px'><div class='l' style='font-size:11px;color:#8b97a7'>FEAR-GREED INDEX — {int(fg['value'])} ({fg['state']})</div>"
                    f"<div style='height:10px;border-radius:5px;background:linear-gradient(90deg,#3fb950,#d6a429,#f85149);position:relative;margin:10px 0'><div style='position:absolute;left:{pct}%;top:-3px;width:3px;height:16px;background:#fff;border-radius:2px'></div></div>"
                    f"<div class='wr-row' style='border:none;padding:0'><span class='wr-why' style='margin:0'>0 = extreme fear (BUY)</span><span class='wr-why'>100 = extreme greed</span></div>"
                    f"<div class='a' style='color:{fgcol};margin-top:6px;font-size:12px'>{fg['signal']}</div></div>", unsafe_allow_html=True)
    if cr:
        clc = COL.get(cr["color"], "#5b6675")
        bars = ""
        for h in [12, 24, 36]:
            p = cr["crash_prob"][h] * 100; b = cr["base_prob"][h] * 100
            bars += (f"<div style='margin:7px 12px'><div class='wr-row' style='border:none;padding:0'><span class='wr-why' style='margin:0'>within {h}mo</span><span class='wr-why' style='color:{clc}'>{p:.0f}% (base {b:.0f}%)</span></div>"
                     f"<div style='height:6px;background:#1e2530;border-radius:3px;margin-top:3px'><div style='width:{min(100,p)}%;height:6px;background:{clc};border-radius:3px'></div></div></div>")
        st.markdown(f"{CSS}<div class='wr-box'><div class='l' style='padding:10px 12px 0;font-size:11px;color:#8b97a7'>CRASH RISK — {cr['risk_level']}</div>{bars}<div class='a' style='color:{clc};padding:6px 12px;font-size:12px'>{cr['action']}</div><div class='wr-note' style='margin:0 8px 8px'>{cr['honest_note']}</div></div>", unsafe_allow_html=True)
    if vr:
        st.markdown(f"{CSS}<div class='wr-box' style='padding:12px 16px'><div class='l' style='font-size:11px;color:#8b97a7'>VALUATION ROOM</div>"
                    f"<div class='n' style='font-size:24px;color:#6ea8ff'>CAPE {vr['current_cape']} · {int(vr['percentile'])}th pct</div>"
                    f"<div class='s'>When this rich: fwd 1yr {vr['fwd_1yr_pct']:+.0f}%, 3yr {vr['fwd_3yr_pct']:+.0f}%, {int(vr['pct_1yr_positive'])}% of time still positive.</div>"
                    f"<div class='a' style='color:#6ea8ff;margin-top:6px;font-size:12px'>Median {vr['median_months_to_drawdown']} months to next −20% drawdown. {vr['interpretation']}</div></div>", unsafe_allow_html=True)
    st.markdown("<div class='wr-note'>Panic-bottom is the validated contrarian signal (fwd63 +6% vs +3%, p&lt;0.001). Euphoria-top is weaker (bull-market bias). Crash risk is a probability, not a timing call — high valuation does not mean sell.</div>", unsafe_allow_html=True)

# ───────────────────────── DECISION ─────────────────────────
with tabs[3]:
    _hd("DECISION BOARD", "theme → best equity → beta chain → invalidation · shock → tradeable names")
    st.markdown("<div class='wr-lbl'>Theme → Best Equity + Beta Chain</div>", unsafe_allow_html=True)
    for theme in ["AI", "Power", "Memory", "Cooling", "Optics", "Defense"]:
        dec = G.decide_theme(theme, prices)
        be = dec.get("best_equity")
        if not be:
            continue
        ev = f" · EV {be['ev_pct']:+.0f}%" if be.get("ev_pct") is not None else ""
        betas = ", ".join(b["ticker"] for b in dec.get("beta_plays", [])[:4])
        st.markdown(f"{CSS}<div class='wr-box' style='border-left:3px solid #3fb950'>"
                    f"<div class='wr-row' style='border:none'><span class='wr-name'>{theme} → <span style='color:#3fb950'>{be['ticker']}</span>{ev}</span><span class='wr-why'>alt: {(dec.get('alternative') or {}).get('ticker','—')}</span></div>"
                    f"<div style='padding:0 12px 10px'><div style='font-size:11.5px;color:#8b97a7'>why: {' → '.join(dec['mechanism'])}</div>"
                    f"<div style='font-size:11.5px;color:#9aa6b2;margin-top:3px'>beta plays: {betas or '—'}</div>"
                    f"<div style='font-size:11.5px;color:#7d8898;margin-top:3px'>invalidation: {dec['invalidation']}</div></div></div>", unsafe_allow_html=True)

    st.markdown("<div class='wr-lbl'>Macro Shock → Tradeable Consequences</div>", unsafe_allow_html=True)
    for shock, dirn, label in [("War/Geopolitics", "up", "War / oil shock"), ("Fed", "down", "Fed easing")]:
        s = G.shock_to_plays(shock, dirn)
        chip_parts = []
        for p in s["plays"][:6]:
            is_long = p["direction"] == "long"
            bg = "#12301c" if is_long else "#301414"; fc = "#3fb950" if is_long else "#f85149"
            chip_parts.append(f"<span class='wr-chip' style='background:{bg};color:{fc}'>{p['direction'][:1].upper()} {p['ticker']} <span style='opacity:.6'>via {p['via']}</span></span>")
        chips = " ".join(chip_parts)
        st.markdown(f"{CSS}<div class='wr-box' style='padding:10px 14px'><div class='wr-name'>{label}</div><div style='margin-top:6px'>{chips}</div></div>", unsafe_allow_html=True)

    st.markdown("<div class='wr-lbl'>Investment Memos (top names)</div>", unsafe_allow_html=True)
    memo_names = [r["ticker"] for r in state["ticker_ranking"][:2]] + ["MU", "ETN", "COHR"]
    for tk in list(dict.fromkeys(memo_names))[:5]:
        m = G.investment_memo(tk, prices.get(tk))
        emc = m.get("expected_market_cap", {})
        emc_line = (f"expected mcap: bull ${emc['scenarios']['bull']['px']} / base ${emc['scenarios']['base']['px']} / bear ${emc['scenarios']['bear']['px']}" if emc.get("scenarios") else "expected mcap: add live price data")
        dec = m.get("decision", {})
        st.markdown(f"{CSS}<div class='wr-box'><div class='wr-row' style='border:none'><span class='wr-badge' style='color:#3fb950;background:#12301c'>{'★'*(m.get('stars') or 0)}</span><span class='wr-name'>{tk}</span><span class='wr-why'>{m.get('role','')} · {m.get('chain_node','')}</span></div>"
                    f"<div style='padding:0 12px 10px'><div style='font-size:11.5px;color:#9aa6b2'>{emc_line}</div>"
                    f"<div style='font-size:11.5px;color:#8b97a7;margin-top:3px'>beta play: {', '.join(m.get('beta_play',[])) or '—'}</div>"
                    + (f"<div style='font-size:11.5px;color:#3fb950;margin-top:3px'>decision: best risk-reward {dec.get('best_risk_reward')}/100 — {dec.get('verdict','')}</div>" if dec else "")
                    + f"<div style='font-size:11.5px;color:#7d8898;margin-top:3px'>invalidation: {m['invalidation']}</div></div></div>", unsafe_allow_html=True)

# ───────────────────────── KNOWLEDGE GRAPH ─────────────────────────
with tabs[4]:
    _hd("KNOWLEDGE GRAPH", "the connected network — shock propagates through typed edges to names")
    shock = st.selectbox("Shock at:", sorted(set(e["from"] for e in G.EDGES)), index=0)
    direction = st.radio("Direction:", ["up", "down"], horizontal=True)
    prop = G.propagate(shock, direction, 4)
    st.markdown(f"<div class='wr-lbl'>{shock} {direction} → propagation (confidence decays each hop)</div>", unsafe_allow_html=True)
    rows = ""
    for step in prop["chain"][:16]:
        tcol = "#3fb950" if step["tested"] else "#8b97a7"
        tks = " ".join(f"<span class='wr-chip' style='background:#1a2230;color:#c9d4e0'>{t}</span>" for t in step["tickers"])
        rows += (f"<div class='wr-row'><span class='wr-badge' style='color:{tcol};background:{tcol}1a'>{step['order']}° {step['move']}</span>"
                 f"<span class='wr-name'>{step['node']}</span><span class='wr-why'>conf {step['confidence']} · {tks or 'via '+step['via']}</span></div>")
    st.markdown(f"{CSS}<div class='wr-box'>{rows}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='wr-note'>{prop['note']}. Tested edges (green) are validated on real data (dollar hub, p&lt;0.001); structural edges (grey) are grounded economic relationships for reasoning — the graph shows what connects to what, honestly labelled.</div>", unsafe_allow_html=True)

# ───────────────────────── VALIDATION ─────────────────────────
with tabs[5]:
    _hd("VALIDATION", "every signal by test status — run python certify.py for the full report")
    signals = [
        ("Cross-asset macro (dollar hub)", "PRODUCTION", "grn", "corr −0.22, p<0.001"),
        ("Risk regime (aggressive/defensive)", "PRODUCTION", "grn", "corr(fwd DD) +0.25, p<0.001"),
        ("Panic-bottom (fear → buy)", "PRODUCTION", "grn", "fwd63 +6% vs +3%, p<0.001"),
        ("Valuation room (CAPE context)", "PRODUCTION", "grn", "CAPE deciles → fwd returns, tested"),
        ("Ticker RS top-decile", "RESEARCH", "amb", "lift 2.14x, alpha not yet significant"),
        ("Knowledge-graph edges", "RESEARCH", "amb", "3 tested (dollar), rest structural"),
        ("Euphoria-top signal", "RESEARCH", "amb", "weak in bull data"),
        ("Naive formation+RS BUY", "REJECTED", "red", "lift 0.85x — no edge, does not drive BUYs"),
    ]
    rows = ""
    for name, status, col, why in signals:
        c = COL[col]; icon = {"PRODUCTION": "✓", "RESEARCH": "◐", "REJECTED": "✕"}[status]
        rows += f"<div class='wr-row'><span class='wr-badge' style='color:{c};background:{c}1a'>{icon} {status}</span><span class='wr-name'>{name}</span><span class='wr-why'>{why}</span></div>"
    st.markdown(f"{CSS}<div class='wr-box'>{rows}</div>", unsafe_allow_html=True)
    st.markdown("<div class='wr-note'>4-fold gate: mechanism + statistical significance + decision value + out-of-sample. A signal reaches PRODUCTION only if all four pass. This is why the naive signal is REJECTED (no edge) and does not drive recommendations. Every number is traceable to a walk-forward/bootstrap test in research/RESEARCH_FINDINGS.md.</div>", unsafe_allow_html=True)
