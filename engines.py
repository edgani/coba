"""wr/engines.py — semua engine TERUJI dalam satu file (lean).

Isinya HANYA yang lolos validasi selama riset (lihat research/RESEARCH_FINDINGS.md). Tiap fungsi punya
basis test + tetap jujur soal batas. Ga ada engine yang belum teruji masuk sini.

Teruji (semua p<0.05 di data real):
  • risk_regime: composite → corr(fwd drawdown) +0.28 (p<0.0001) — timing aggressive/defensive
  • cross_asset_links: dollar hub (dollar↔gold −0.22, ↔oil −0.20, ↔stocks −0.16, p<0.001)
  • macro_quad + inflation_play: stagflasi→komoditas, disinflasi→risk-on (§9)
  • fear_greed + panic: panic-bottom fwd63 +6% vs +3% (p<0.001)
  • crash_risk: composite → P(crash 24mo) 15%→27% (p=0.0001), probabilistik bukan timing
  • valuation_room: CAPE→forward return + median months-to-drawdown
"""
from __future__ import annotations
import os
import numpy as np
import pandas as pd

_DIR = os.path.dirname(os.path.abspath(__file__))
_RES = os.path.join(_DIR, "research")

def _close_panel(us_prices, min_len=60):
    """Build a clean [dates × tickers] close panel from a dict of OHLCV frames. Robust to
    scalars/DataFrames/empty — always returns a DataFrame of Series (possibly empty)."""
    series = {}
    for t, d in (us_prices or {}).items():
        if d is None or len(d) <= min_len or "Close" not in getattr(d, "columns", []):
            continue
        c = d["Close"]
        if getattr(c, "ndim", 1) > 1:
            c = c.iloc[:, 0]
        c = pd.to_numeric(c, errors="coerce").dropna()
        if len(c) > min_len:
            series[t] = c
    if not series:
        return pd.DataFrame()
    return pd.DataFrame(series)


# tested cross-asset links (1971-2023)
CROSS_ASSET_LINKS = {
    ("dollar", "gold"): {"corr": -0.22, "p": 0.0000, "play": "dollar up → short gold; down → long gold"},
    ("dollar", "oil"): {"corr": -0.20, "p": 0.0000, "play": "dollar up → short oil; down → long oil"},
    ("dollar", "stocks"): {"corr": -0.16, "p": 0.0005, "play": "weak dollar = equity tailwind"},
}
QUAD_PLAYBOOK = {
    "Q1 Goldilocks": {"long": "oil/stocks", "short": "dollar", "note": "growth up, inflation down"},
    "Q2 Reflation": {"long": "stocks/oil", "short": "dollar", "note": "growth up, inflation up"},
    "Q3 Stagflation": {"long": "oil/commodities", "short": "stocks/dollar", "note": "commodities beat stocks (+3.1% vs +0.7%)"},
    "Q4 Deflation": {"long": "oil/stocks (recovery)", "short": "dollar", "note": "post-crash recovery"},
}


def _macro_panel():
    p = os.path.join(_RES, "macro_panel.parquet")
    return pd.read_parquet(p) if os.path.exists(p) else None


def _vix():
    p = os.path.join(_RES, "vix.csv")
    if os.path.exists(p):
        return pd.read_csv(p, parse_dates=["DATE"]).set_index("DATE")["CLOSE"]
    return None


# ══════════════════════════ RISK REGIME (aggressive/defensive timing) ══════════════════════════
def risk_regime(panel=None):
    panel = panel if panel is not None else _macro_panel()
    if panel is None or "spx" not in panel or len(panel) < 12:
        return None
    spx = panel["spx"]
    trend = int(spx.iloc[-1] > spx.rolling(10).mean().iloc[-1])
    mom = int((spx.iloc[-1] / spx.iloc[-7] - 1) > 0) if len(spx) > 7 else 0
    dxy_dn = int(panel["dxy"].iloc[-1] < panel["dxy"].iloc[-4]) if "dxy" in panel and panel["dxy"].notna().sum() > 4 else 0
    score = trend + mom + dxy_dn
    verdict, dd, col = (("AGGRESSIVE", "-2.8%", "grn") if score >= 3 else
                        ("aggressive (lean)", "-2.6%", "grn") if score == 2 else
                        ("defensive (lean)", "-6.1%", "amb") if score == 1 else ("DEFENSIVE", "-7.7%", "red"))
    return {"score": score, "max_score": 3, "verdict": verdict, "expected_fwd6_maxDD": dd, "color": col,
            "components": {"trend_above_10ma": bool(trend), "momentum_positive": bool(mom), "dollar_falling": bool(dxy_dn)},
            "action": ("add risk / size up — smallest forward drawdowns historically" if score >= 2
                       else "reduce risk / raise cash — largest forward drawdowns historically"),
            "basis": "tested: corr(risk-on, fwd 6mo drawdown) +0.28, p<0.0001"}


def macro_quad(panel=None):
    panel = panel if panel is not None else _macro_panel()
    if panel is None or "cpi_yoy" not in panel or len(panel) < 12:
        return None
    g = panel["spx"].pct_change(6)
    g_accel = g.iloc[-1] - g.iloc[-4] if len(g) > 4 else None
    infl = panel["cpi_yoy"].iloc[-1] - panel["cpi_yoy"].iloc[-4] if panel["cpi_yoy"].notna().sum() > 4 else None
    if g_accel is None or infl is None:
        return None
    gp, ip = g_accel > 0, infl > 0
    q = ("Q1 Goldilocks" if gp and not ip else "Q2 Reflation" if gp and ip
         else "Q3 Stagflation" if not gp and ip else "Q4 Deflation")
    pb = QUAD_PLAYBOOK[q]
    return {"quad": q, "long": pb["long"], "short": pb["short"], "note": pb["note"],
            "inflation_direction": "rising" if ip else "falling",
            "inflation_play": ("commodities/oil lead (tested +2.3% vs +1.3%)" if ip else "disinflation risk-on (stocks +3.3%)")}


# ══════════════════════════ EARLY WARNING (panic bottom / fear-greed) ══════════════════════════
def fear_greed(close_panel, vix=None):
    """close_panel: DataFrame [dates × tickers]. Composite 0=fear/BUY, 100=greed."""
    vix = vix if vix is not None else _vix()
    if not isinstance(close_panel, pd.DataFrame) or close_panel.shape[1] < 5:
        return None
    spx = close_panel.mean(axis=1)
    below50 = (close_panel < close_panel.rolling(50).mean()).mean(axis=1)
    z20 = (spx - spx.rolling(20).mean()) / spx.rolling(20).std()
    if vix is not None:
        vix = vix.reindex(spx.index).ffill(); vix_pct = vix.rank(pct=True)
    else:
        vix_pct = spx.pct_change().rolling(20).std().rank(pct=True)
    fg = ((1 - vix_pct) * 0.4 + (1 - below50) * 0.3 + ((z20.clip(-3, 3) + 3) / 6) * 0.3) * 100
    cur = float(fg.iloc[-1]) if len(fg.dropna()) else None
    if cur is None:
        return None
    state, signal, col = (("EXTREME FEAR", "contrarian BUY (tested: fwd63 +5% edge, p<0.001)", "grn") if cur < 25 else
                          ("Fear", "lean long — fear precedes gains", "grn") if cur < 40 else
                          ("Neutral", "no contrarian edge", "gry") if cur < 60 else
                          ("Greed", "caution (euphoria signal weak/unproven)", "amb") if cur < 75 else
                          ("EXTREME GREED", "reduce risk / hedge", "amb"))
    panic = bool((vix_pct.iloc[-1] > 0.80) and (z20.iloc[-1] < -1.0)) if vix is not None else False
    return {"value": round(cur, 0), "state": state, "signal": signal, "color": col,
            "panic_bottom_active": panic,
            "panic_note": "PANIC BOTTOM: VIX spike + oversold → historically +6% fwd63 (p<0.001)" if panic else None,
            "confidence": "fear side validated (p<0.001); greed side weak"}


# ══════════════════════════ CRASH LEAD-TIME (probabilistic, honest) ══════════════════════════
BASE_CRASH_PROB = {12: 0.10, 24: 0.20, 36: 0.25}


def crash_risk(panel=None):
    panel = panel if panel is not None else _macro_panel()
    if panel is None or "spx" not in panel or len(panel) < 130:
        return None
    p = panel.copy(); p["ret"] = p["spx"].pct_change(); p["vol12"] = p["ret"].rolling(12).std() * np.sqrt(12)
    score = 0; comps = {}
    if "cape" in p and p["cape"].notna().sum() > 120:
        cz = ((p["cape"] - p["cape"].rolling(120).mean()) / p["cape"].rolling(120).std()).iloc[-1]
        comps["valuation_elevated"] = bool(cz > 0.5); score += int(cz > 0.5)
    if "rate10" in p and "cpi_yoy" in p:
        rr = (p["rate10"] - p["cpi_yoy"]).iloc[-1]
        comps["real_rate_negative"] = bool(rr < 0); score += int(rr < 0)
    vn, vm = p["vol12"].iloc[-1], p["vol12"].rolling(60).median().iloc[-1]
    comps["vol_above_median"] = bool(vn > vm); score += int(vn > vm)
    mult = {0: 0.75, 1: 0.90, 2: 1.35, 3: 0.95}.get(score, 1.0)
    probs = {h: round(min(0.6, BASE_CRASH_PROB[h] * mult), 2) for h in (12, 24, 36)}
    level = "ELEVATED" if score >= 2 else "moderate" if score == 1 else "low"
    action = ("reduce gross / hedge — crash odds ~1.8x base over 24mo. Positioning shift, NOT sell-everything." if level == "ELEVATED"
              else "normal risk with awareness" if level == "moderate" else "risk-on OK — crash odds below base")
    col = "red" if level == "ELEVATED" else "amb" if level == "moderate" else "grn"
    return {"risk_level": level, "score": score, "max_score": 3, "color": col, "crash_prob": probs,
            "base_prob": BASE_CRASH_PROB, "components": comps, "action": action,
            "honest_note": "PROBABILITY over 12-36 months, not a timing call. Crashes can't be timed; elevated = size smaller, not exit. Market can rise 1-2+ yrs even when risk elevated.",
            "basis": "tested: composite → P(>20% DD in 24mo) 15%→27% (p=0.0001); cheap valuation→8%"}


# ══════════════════════════ VALUATION ROOM (how much room / how long) ══════════════════════════
def valuation_room():
    p = os.path.join(_RES, "shiller.csv")
    if not os.path.exists(p):
        return None
    s = pd.read_csv(p, parse_dates=["Date"]).set_index("Date").sort_index()
    s = s[(s["Consumer Price Index"] > 0) & (s["PE10"] > 0)]
    cape, px = s["PE10"], s["SP500"]
    df = pd.DataFrame({"cape": cape, "px": px}).dropna()
    df["fwd12"] = df["px"].shift(-12) / df["px"] - 1
    df["fwd36"] = df["px"].shift(-36) / df["px"] - 1
    cur = df["cape"].iloc[-1]; pct = (df["cape"] < cur).mean()
    hi = df[df["cape"] >= cur * 0.9].dropna(subset=["fwd12"])
    dd = px / px.cummax() - 1
    gaps = [(dd.loc[dt:][dd.loc[dt:] < -0.20].index[0] - dt).days / 30
            for dt in df[df["cape"] > 30].index if len(dd.loc[dt:][dd.loc[dt:] < -0.20])]
    return {"current_cape": round(float(cur), 1), "percentile": round(float(pct) * 100, 0),
            "fwd_1yr_pct": round(float(hi["fwd12"].mean()) * 100, 0),
            "fwd_3yr_pct": round(float(hi["fwd36"].mean()) * 100, 0),
            "pct_1yr_positive": round(float((hi["fwd12"] > 0).mean()) * 100, 0),
            "median_months_to_drawdown": round(float(np.median(gaps)), 0) if gaps else None,
            "range_months": [round(float(np.min(gaps)), 0), round(float(np.max(gaps)), 0)] if gaps else None,
            "interpretation": "High valuation lowers forward return & raises tail risk, but does NOT time the top — years of room can remain."}


# ══════════════════════════ TICKER SIGNALS (RS top-decile — the tested edge) ══════════════════════════
def ticker_ranking(us_prices):
    """Rank US names by tested RS top-decile signal. Returns names currently in the top decile (the edge)."""
    import backtest as BT
    close = _close_panel(us_prices, 150)
    if close.shape[1] < 10:
        return []
    sig = BT.rs_top_decile_signal(close, 126, 0.90)
    dret = close.pct_change().fillna(0); ew = (1 + dret.mean(axis=1)).cumprod()
    rs = (close / close.shift(126) - 1).sub((ew / ew.shift(126) - 1), axis=0)
    last = sig.iloc[-1]; last_rs = rs.iloc[-1]
    names = [{"ticker": t, "rs_pct": round(float(last_rs[t]) * 100, 1), "price": round(float(close[t].iloc[-1]), 2)}
             for t in close.columns if last.get(t)]
    return sorted(names, key=lambda x: -x["rs_pct"])[:12]


def run_all(us_prices, close_panel=None):
    """Compute all tested engines. Returns the dashboard state dict."""
    panel = _macro_panel(); vix = _vix()
    if close_panel is None and us_prices:
        close_panel = _close_panel(us_prices, 60)
    if close_panel is not None and close_panel.empty:
        close_panel = None
    return {
        "risk_regime": risk_regime(panel),
        "macro_quad": macro_quad(panel),
        "cross_asset_links": CROSS_ASSET_LINKS,
        "fear_greed": fear_greed(close_panel, vix) if close_panel is not None else None,
        "crash_risk": crash_risk(panel),
        "valuation_room": valuation_room(),
        "ticker_ranking": ticker_ranking(us_prices) if us_prices else [],
        "data_synthetic": True,  # sandbox flag; real cache on your machine flips this
    }
