"""wr/graph.py — knowledge graph + decision + memo + thesis (lean, consolidated).

Ini connective tissue yang bikin "OS bukan kumpulan engine": satu directed network macro→supply-chain→
company, propagasi shock 2nd/3rd/4th order, lalu theme→best equity→beta→invalidation, dan tiap ticker
sebagai Investment Memo (bukan watchlist).

JUJUR: edge tested=True hanya cross-asset (dollar-hub, p<0.001). Sisanya structural knowledge (hubungan
ekonomi grounded), ditandai tested=False — peta reasoning, bukan klaim statistik. Expected market cap
butuh data harga (mesin lu).
"""
from __future__ import annotations
import os, json
from collections import defaultdict

_DIR = os.path.dirname(os.path.abspath(__file__))


# ── EDGES: (from, to, sign, lead_days, confidence, tested, evidence) ──
def _e(f, t, s, lead, conf, tested, ev):
    return {"from": f, "to": t, "sign": s, "lead_days": lead, "confidence": conf, "tested": tested, "evidence": ev}

EDGES = [
    # cross-asset (TESTED, p<0.001)
    _e("Dollar", "Gold", -1, 0, 0.8, True, "corr -0.22, p<0.001"),
    _e("Dollar", "Oil", -1, 0, 0.75, True, "corr -0.20, p<0.001"),
    _e("Dollar", "US Equities", -1, 0, 0.6, True, "corr -0.16, p<0.001"),
    _e("Dollar", "EM Equities", -1, 0, 0.7, False, "structural: strong dollar pressures EM"),
    # War / geopolitics (structural)
    _e("War/Geopolitics", "Oil", 1, 5, 0.7, False, "supply risk premium"),
    _e("Oil", "Refinery", 1, 10, 0.6, False, "feedstock"),
    _e("Refinery", "Crack Spread", 1, 10, 0.5, False, "refining margin"),
    _e("Oil", "Tanker/Shipping", 1, 15, 0.55, False, "transport demand"),
    _e("Tanker/Shipping", "Freight Rates", 1, 20, 0.5, False, "capacity"),
    _e("Freight Rates", "Goods Inflation", 1, 60, 0.45, False, "cost pass-through"),
    _e("Goods Inflation", "Rates", 1, 90, 0.5, False, "policy response"),
    _e("Rates", "Growth", -1, 180, 0.5, False, "financial conditions"),
    _e("Oil", "Shipyard", 1, 60, 0.4, False, "capex cycle"),
    _e("Shipyard", "Steel", 1, 30, 0.5, False, "input"),
    _e("Steel", "Iron Ore", 1, 20, 0.6, False, "input"),
    # AI compute deep chain (structural)
    _e("AI/Compute", "HBM", 1, 30, 0.75, False, "memory demand"),
    _e("HBM", "DRAM", 1, 20, 0.7, False, "wafer allocation"),
    _e("HBM", "TSV", 1, 20, 0.65, False, "packaging"),
    _e("TSV", "Advanced Packaging", 1, 30, 0.65, False, "assembly"),
    _e("Advanced Packaging", "CoWoS", 1, 30, 0.7, False, "TSMC capacity"),
    _e("CoWoS", "Substrate", 1, 40, 0.6, False, "material"),
    _e("Substrate", "ABF", 1, 40, 0.55, False, "film"),
    _e("AI/Compute", "Power", 1, 60, 0.7, False, "datacenter power"),
    _e("Power", "Transformer", 1, 90, 0.65, False, "grid interconnect"),
    _e("Transformer", "Copper", 1, 30, 0.6, False, "windings"),
    _e("Power", "Utility", 1, 60, 0.6, False, "demand"),
    _e("Utility", "Nuclear", 1, 180, 0.5, False, "baseload"),
    _e("Nuclear", "Uranium", 1, 90, 0.6, False, "fuel"),
    _e("AI/Compute", "Cooling", 1, 45, 0.65, False, "thermal"),
    _e("AI/Compute", "Optics/Photonics", 1, 30, 0.7, False, "interconnect"),
    _e("AI/Compute", "Networking", 1, 30, 0.7, False, "fabric"),
    # policy / central bank (mixed)
    _e("Tariff", "Manufacturing", -1, 90, 0.5, False, "cost/reshoring"),
    _e("Tariff", "Dollar", 1, 30, 0.4, False, "trade balance"),
    _e("Fed", "Dollar", 1, 5, 0.55, False, "rate differential"),
    _e("Fed", "US Rates", 1, 1, 0.8, False, "policy rate"),
    _e("US Rates", "Global Liquidity", -1, 30, 0.6, False, "dollar funding"),
    _e("Global Liquidity", "Risk Assets", 1, 30, 0.6, False, "flows"),
    _e("PBOC", "Copper", 1, 60, 0.5, False, "China stimulus"),
    # defense theme
    _e("Defense", "Drone", 1, 60, 0.6, False, "procurement"),
    _e("Drone", "Sensor", 1, 30, 0.55, False, "components"),
    _e("Defense", "Rare Earth", 1, 90, 0.5, False, "materials"),
]

# node → tradeable tickers (from your research)
NODE_TICKERS = {
    "HBM": ["MU"], "DRAM": ["MU"], "CoWoS": ["TSM"], "Advanced Packaging": ["AMKR", "ASE"],
    "Optics/Photonics": ["COHR", "LITE", "AAOI", "CRDO"], "Networking": ["ANET", "AVGO", "CRDO"],
    "Power": ["ETN", "GEV", "POWL"], "Transformer": ["ETN", "GEV"], "Copper": ["FCX"],
    "Utility": ["CEG", "VST"], "Nuclear": ["CEG", "LEU"], "Uranium": ["CCJ", "LEU"],
    "Cooling": ["VRT"], "Oil": ["XOM", "CVX"], "Refinery": ["VLO", "MPC"], "Steel": ["NUE", "STLD"],
    "Iron Ore": ["BHP", "RIO"], "Gold": ["GLD", "NEM"], "AI/Compute": ["NVDA", "AVGO"],
    "Defense": ["LMT", "RTX"], "Drone": ["AVAV"], "Rare Earth": ["MP"],
}

_ADJ = defaultdict(list)
for e in EDGES:
    _ADJ[e["from"]].append(e)


def propagate(shock_node, direction="up", max_hops=4, min_conf=0.15):
    """Shock → ordered downstream consequences (2nd/3rd/4th order), confidence decays each hop."""
    start = 1 if direction == "up" else -1
    results, visited = [], {}
    frontier = [(shock_node, start, 1.0, [shock_node], 0)]
    while frontier:
        node, sign, cum, path, hop = frontier.pop(0)
        if hop >= max_hops:
            continue
        for e in _ADJ.get(node, []):
            nxt = e["to"]; ns = sign * e["sign"]; nc = cum * e["confidence"]
            if nc < min_conf or (nxt in visited and visited[nxt] >= nc):
                continue
            visited[nxt] = nc
            results.append({"order": hop + 1, "node": nxt, "move": "↑" if ns > 0 else "↓",
                            "confidence": round(nc, 2), "via": node, "tested": e["tested"],
                            "tickers": NODE_TICKERS.get(nxt, []), "path": " → ".join(path + [nxt])})
            frontier.append((nxt, ns, nc, path + [nxt], hop + 1))
    results.sort(key=lambda x: (x["order"], -x["confidence"]))
    return {"shock": f"{shock_node} {direction}", "chain": results,
            "note": "confidence decays each hop; tested edges validated (p<0.001), others structural knowledge"}


def beta_chain(theme_node, max_hops=3):
    """Theme → downstream picks by derivative order (picks & shovels / hidden winners)."""
    prop = propagate(theme_node, "up", max_hops)
    picks = defaultdict(list)
    for step in prop["chain"]:
        for tk in step["tickers"]:
            picks[step["order"]].append({"ticker": tk, "node": step["node"]})
    return {"primary": picks.get(1, []), "second": picks.get(2, []), "third": picks.get(3, [])}


# ── theme → entry node ──
THEME_NODE = {"AI": "AI/Compute", "Power": "Power", "Memory": "HBM", "Cooling": "Cooling",
              "Optics": "Optics/Photonics", "Defense": "Defense", "Nuclear": "Nuclear"}


def decide_theme(theme, prices=None):
    """Theme → best equity + beta chain + invalidation + alternative."""
    node = THEME_NODE.get(theme, theme)
    bc = beta_chain(node, 3)
    cands = []
    seen = set()
    for order, items in [(1, bc["primary"]), (2, bc["second"]), (3, bc["third"])]:
        for it in items:
            tk = it["ticker"]
            if tk in seen:
                continue
            seen.add(tk)
            ev = _ev(tk, prices.get(tk)) if prices and prices.get(tk) else None
            cands.append({"ticker": tk, "order": order, "node": it["node"], "ev_pct": ev})
    ranked = sorted(cands, key=lambda c: (-(c["ev_pct"] if c["ev_pct"] is not None else -999), c["order"]))
    best = ranked[0] if ranked else None
    alt = ranked[1] if len(ranked) > 1 else None
    mech = [node] + list(dict.fromkeys([i["node"] for i in bc["second"] + bc["third"]]))[:4]
    return {"theme": theme, "best_equity": best, "alternative": alt,
            "beta_plays": [c for c in ranked if c not in (best, alt)][:4], "mechanism": mech,
            "invalidation": f"{node} demand stalls / upstream driver reverses (AI capex cut, rate shock)"}


def shock_to_plays(shock_node, direction="up"):
    prop = propagate(shock_node, direction, 4)
    plays = []
    for step in prop["chain"]:
        for tk in step["tickers"]:
            plays.append({"ticker": tk, "via": step["via"], "order": step["order"],
                          "direction": "long" if step["move"] == "↑" else "short", "confidence": step["confidence"]})
    return {"shock": f"{shock_node} {direction}", "plays": plays[:12]}


# ── Expected market cap / convexity (scenario-based) ──
_SCN = {"bull": (0.30, 2.0), "base": (0.50, 1.35), "bear": (0.20, 0.55)}  # prob, price-multiple


def _ev(ticker, price):
    """Simple expected-value from bull/base/bear scenarios (needs price)."""
    if not price:
        return None
    ev = sum(p * (m - 1) for (p, m) in _SCN.values()) * 100
    return round(ev, 0)


def expected_market_cap(ticker, price, market_cap=None):
    if not price:
        return {"note": "needs price (add via data.add_ticker)"}
    scn = {k: {"px": round(price * m, 2), "prob": p} for k, (p, m) in _SCN.items()}
    ev = _ev(ticker, price)
    tail = (_SCN["bull"][1] - 1) / (1 - _SCN["bear"][1]) if (1 - _SCN["bear"][1]) else None
    return {"scenarios": scn, "ev_pct": ev, "tail_ratio": round(tail, 2) if tail else None}


# ── Investment Memo ──
_REF = None
def _ref():
    global _REF
    if _REF is None:
        try:
            _REF = json.load(open(os.path.join(_DIR, "data", "bottleneck_reference.json")))
        except Exception:
            _REF = {}
    return _REF


def investment_memo(ticker, price=None, market_cap=None):
    ref = _ref(); tk = ticker.upper(); out = {"ticker": tk}
    rec = next((r for r in ref.get("consensus_heatmap", []) if (r.get("ticker") or "").upper() == tk), None)
    if rec:
        out.update({"role": rec.get("role"), "layer": rec.get("layer"), "stars": rec.get("stars")})
    node = next((n for n, tks in NODE_TICKERS.items() if tk in tks), None)
    if node:
        out["chain_node"] = node
        out["supply_drivers"] = [e["from"] for e in EDGES if e["to"] == node][:4]
        out["demand_drivers"] = [e["to"] for e in _ADJ.get(node, [])][:4]
        bc = beta_chain(node, 2)
        out["beta_play"] = list(dict.fromkeys([b["ticker"] for b in bc["primary"] + bc["second"]]))[:5]
    emc = expected_market_cap(tk, price, market_cap)
    out["expected_market_cap"] = emc
    if emc.get("ev_pct") is not None:
        rr = max(0, min(100, int(50 + emc["ev_pct"] * 0.4 + (emc.get("tail_ratio") or 1) * 5)))
        out["decision"] = {"best_risk_reward": rr, "verdict": ("STRONG accumulation" if rr >= 75 else "moderate — selective" if rr >= 55 else "low reward — wait"),
                           "note": "score from expected-mcap convexity, not a buy signal"}
    cats = [c for c in ref.get("catalyst_timeline", []) if (c.get("ticker") or "").upper() == tk]
    if cats:
        out["catalysts"] = [{"quarter": c.get("quarter"), "event": c.get("event")} for c in cats[:2]]
    out["invalidation"] = "thesis driver reverses (demand cut / supply catch-up / margin compression)"
    return out


# ── Thesis + Playbook ──
THESES = {
    "AI Capex Cycle": {"hypothesis": "AI capex grows >25%/yr through 2028, cascading down compute+power chain",
                       "mechanism": "AI → HBM → Packaging → Power → Transformer → Cooling", "probability": 0.78,
                       "beneficiaries": ["MU", "AVGO", "ETN", "GEV", "VRT", "COHR"], "horizon": "2026-2028",
                       "invalidation": "hyperscaler capex cut, or AI ROI disappoints", "status": "ACTIVE"},
    "Power / Electrification": {"hypothesis": "Structural power shortage drives multi-year capex",
                                "mechanism": "Power → Transformer → Copper → Utility → Nuclear → Uranium", "probability": 0.74,
                                "beneficiaries": ["ETN", "GEV", "POWL", "VRT", "CEG"], "horizon": "2025-2030",
                                "invalidation": "demand slows (recession) or supply catches up", "status": "ACTIVE"},
    "Memory / HBM": {"hypothesis": "HBM stays tight vs AI demand → pricing power for memory",
                     "mechanism": "AI → HBM demand → DRAM/TSV bottleneck → ASP up → margins up", "probability": 0.68,
                     "beneficiaries": ["MU"], "horizon": "2026-2027",
                     "invalidation": "Samsung catches up on HBM → oversupply", "status": "ACTIVE"},
}
PLAYBOOKS = {
    "War / Geopolitics": [("Phase 1", "Oil, Gold, Defense rally; risk-off"), ("Phase 2", "Freight+inflation rise"),
                          ("Phase 3", "Rates react; dollar strength"), ("Phase 4", "Growth/consumer weaken")],
    "Inflation Rising": [("Phase 1", "Commodities+oil lead (tested +2.3% vs +1.3%)"), ("Phase 2", "Rates rise"),
                         ("Phase 3", "Dollar firms"), ("Phase 4", "Growth slows if rates overshoot")],
    "Disinflation": [("Phase 1", "Risk-on: stocks +3.3%, oil +3.8% (tested)"), ("Phase 2", "Rates fall; tech leads"),
                     ("Phase 3", "Dollar softens; EM+gold benefit")],
    "Crash / Risk-off": [("Phase 1", "Raise cash; reduce beta"), ("Phase 2", "Hedge; quality outperforms"),
                         ("Phase 3", "Panic-bottom → contrarian BUY (tested +6% p<0.001)"), ("Phase 4", "RS top-decile leads bounce")],
}


def devils_advocate(theme):
    t = THESES.get(theme) or next((v for k, v in THESES.items() if theme.lower() in k.lower()), None)
    base = t["invalidation"] if t else "demand assumption wrong"
    return [base, "consensus already positioned → edge decayed", "capex cycle turns to oversupply",
            "cheaper 2nd-derivative play captures more of the move"]


# ═══ RICH INTELLIGENCE ACCESSORS (surface the curated research — brought back from old warroom) ═══
def supply_chain_layers():
    """Photonics/AI 12-layer supply chain with leader, monopoly strength, geopolitical risk."""
    return _ref().get("photonics_12_layer", [])

def companies_by_layer():
    """68 consensus names grouped by supply-chain layer (role, stars, target, priority)."""
    ch = _ref().get("consensus_heatmap", [])
    by = {}
    for r in ch:
        by.setdefault(r.get("layer", "Other"), []).append(r)
    for k in by:
        by[k] = sorted(by[k], key=lambda x: -(x.get("stars", 0) or 0))
    return dict(sorted(by.items(), key=lambda kv: -max((r.get("stars", 0) or 0) for r in kv[1])))

def all_companies():
    return sorted(_ref().get("consensus_heatmap", []), key=lambda x: -(x.get("stars", 0) or 0))

def catalysts():
    return sorted(_ref().get("catalyst_timeline", []), key=lambda x: str(x.get("quarter", "")))

def rotation_phases():
    return _ref().get("institutional_rotation", [])

def ma_watchlist():
    return _ref().get("ma_watchlist", [])

def risk_flags():
    return _ref().get("risk_flags", [])

def behavioral_macro():
    return _ref().get("behavioral_macro", {})

def nvidia_playbook():
    return _ref().get("nvidia_playbook", {})

def market_cap_opportunity(ticker, price=None):
    """Current → intrinsic → bull → extreme framing (the opportunity gap, not target price)."""
    rec = next((r for r in _ref().get("consensus_heatmap", []) if (r.get("ticker") or "").upper() == ticker.upper()), None)
    emc = expected_market_cap(ticker, price) if price else {}
    scn = emc.get("scenarios", {})
    return {"ticker": ticker.upper(), "role": rec.get("role") if rec else None,
            "target_hint": rec.get("target") if rec else None,
            "current_px": price, "scenarios": scn, "ev_pct": emc.get("ev_pct"),
            "note": "opportunity = gap between current and scenario-based future value, with probability — not a price target"}

def multi_level_beta(theme):
    """Explicit multi-level beta chain: primary (1x) → 2nd order → 3rd order, with tickers at each level."""
    node = THEME_NODE.get(theme, theme)
    bc = beta_chain(node, 3)
    return {"theme": theme, "entry": node,
            "levels": [{"order": 1, "label": "Primary (direct)", "picks": bc["primary"]},
                       {"order": 2, "label": "2nd order (supplier/enabler)", "picks": bc["second"]},
                       {"order": 3, "label": "3rd order (deep/hidden)", "picks": bc["third"]}],
            "note": "beta rises down the chain — 3rd-order names move more but carry more risk (higher convexity, lower liquidity)"}
