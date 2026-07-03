"""warroom/attention.py — Today's Attention (blueprint #396 Human Attention Optimizer).

Filosofi Edward: "Dashboard jangan bikin lu baca 300 widget. Hari ini lu cuma perlu liat 6 hal."
Engine ini BUKAN indikator baru — dia baca engine yang UDAH ada (regime, meters, crash, rotation,
conviction, country grid, decision market) lalu ambil yang paling butuh perhatian HARI INI, ranked by
magnitude perubahan / extremity. Sisanya collapse.

Tiap item: judul, status, arah (naik/turun/breakout/confirm), dan skor urgency 0-100. Semua diturunkan
dari nilai engine yang ada — ga ada angka karangan. Kalau ga ada yang ekstrem, dia bilang "quiet day".
"""
from __future__ import annotations


def _urg(v, lo, hi):
    """Map a value's distance from neutral to 0-100 urgency."""
    if v is None:
        return 0
    try:
        v = float(v)
    except Exception:
        return 0
    mid = (lo + hi) / 2
    span = (hi - lo) / 2 or 1
    return int(max(0, min(100, abs(v - mid) / span * 100)))


def build(d):
    items = []
    reg = d.get("regime") or {}
    crash = d.get("crash") or {}
    cr = d.get("cycle_rotation") or {}
    mc = d.get("meters_computed") or {}
    conv = d.get("conviction") or []
    cg = d.get("country_regime") or {}
    dm = d.get("decision_market") or {}
    ew = d.get("early_warning") or {}

    # 0. PANIC BOTTOM (validated contrarian, p<0.001) — highest priority when active
    panic = ew.get("panic") or {}
    if panic.get("active"):
        items.append({"title": "⚠ PANIC BOTTOM setup", "status": f"VIX {panic.get('vix_pct'):.0f}pct · {panic.get('breadth_below_50ma',0):.0f}% below 50ma",
                      "arrow": f"contrarian BUY · {panic.get('expected_fwd63','')}", "urg": 95, "color": "grn"})
    fg = ew.get("fear_greed") or {}
    if fg.get("value") is not None and (fg["value"] < 30 or fg["value"] > 75):
        items.append({"title": f"Fear-Greed {fg['value']:.0f}", "status": fg.get("state", ""),
                      "arrow": fg.get("signal", "")[:48], "urg": int(abs(fg["value"] - 50) * 1.6),
                      "color": fg.get("color", "amb")})

    # 1. Crash risk (high pressure = urgent)
    cp = crash.get("pressure")
    if isinstance(cp, (int, float)):
        arrow = "↑ RISING" if cp >= 55 else "↓ calm" if cp < 35 else "→ neutral"
        items.append({"title": "Crash Risk", "status": f"{crash.get('type','—')} ({cp:.0f}/100)",
                      "arrow": arrow, "urg": _urg(cp, 0, 100) if cp >= 50 else int(cp * 0.4),
                      "color": "red" if cp >= 55 else "amb" if cp >= 35 else "grn"})

    # 2. Liquidity regime
    liq = mc.get("liquidity") or {}
    if liq.get("value") is not None:
        v = liq["value"]
        items.append({"title": "Liquidity", "status": liq.get("status", "—"),
                      "arrow": "↑ ample" if v >= 60 else "↓ tightening" if v < 40 else "→ neutral",
                      "urg": _urg(v, 0, 100), "color": liq.get("color", "amb")})

    # 3. Credit stress
    cred = mc.get("credit") or {}
    if cred.get("value") is not None:
        v = cred["value"]
        if v < 45 or v > 70:  # only surface if notable
            items.append({"title": "Credit", "status": cred.get("status", "—"),
                          "arrow": "↓ stress widening" if v < 45 else "↑ risk-on",
                          "urg": _urg(v, 0, 100), "color": cred.get("color", "amb")})

    # 4. Rotation compass
    sc = cr.get("score")
    if isinstance(sc, (int, float)):
        items.append({"title": "Money Rotation", "status": cr.get("compass", "—"),
                      "arrow": cr.get("compass", ""), "urg": min(100, int(abs(sc) / (cr.get("n_axes") or 7) * 100) + 20),
                      "color": cr.get("color", "amb")})

    # 5. Bubble / froth
    bub = mc.get("bubble") or {}
    if bub.get("value") is not None and bub["value"] >= 60:
        items.append({"title": "Froth / Bubble", "status": bub.get("status", "—"),
                      "arrow": "↑ late-stage", "urg": _urg(bub["value"], 40, 100), "color": "red"})

    # 6. Top conviction name with best convexity
    best = None
    for r in conv:
        cx = ((r.get("decision_pkg") or {}).get("mcap_target") or {}).get("convexity") or {}
        if cx.get("ev_pct") is not None and (best is None or cx["ev_pct"] > best[1]):
            best = (r, cx["ev_pct"], r.get("_dir"))
    if best:
        r, ev, dr = best
        items.append({"title": f"Top Setup · {r.get('ticker')}", "status": f"{dr} · EV {ev:+.0f}%",
                      "arrow": "▲ asymmetric" if ev > 50 else "→ moderate", "urg": min(100, int(abs(ev))),
                      "color": "grn" if ev > 0 else "red"})

    # 7. Country regime standout (any at extreme)
    cells = cg.get("cells") or []
    gl = [c for c in cells if c.get("state") == "goldilocks"]
    df = [c for c in cells if c.get("state") == "deflation"]
    if gl:
        items.append({"title": "Global Regime", "status": f"{len(gl)} Goldilocks · {len(df)} Deflation",
                      "arrow": f"lead: {gl[0]['country']}", "urg": 45, "color": "inf"})

    # 8. Decision market — where the best thesis is
    if dm:
        best_thesis = None
        for thk, mkt in dm.items():
            fr = (mkt.get("frontier") or {}).get("max_ev") or {}
            cands = mkt.get("candidates") or []
            if cands:
                top_ev = cands[0].get("ev_pct", 0)
                if best_thesis is None or top_ev > best_thesis[1]:
                    best_thesis = (thk, top_ev, fr.get("ticker"))
        if best_thesis and best_thesis[1] > 30:
            from warroom.render import _THESIS_TITLE  # reuse titles
            title = _THESIS_TITLE.get(best_thesis[0], best_thesis[0]) if "_THESIS_TITLE" in dir(__import__("warroom.render", fromlist=["_THESIS_TITLE"])) else best_thesis[0]
            items.append({"title": "Best Thesis", "status": f"{title} · {best_thesis[2]}",
                          "arrow": f"EV {best_thesis[1]:+.0f}%", "urg": min(100, int(best_thesis[1])), "color": "grn"})

    items.sort(key=lambda x: -x["urg"])
    top = items[:6]
    return {"items": top, "collapsed": max(0, len(items) - 6),
            "quiet": len([i for i in top if i["urg"] >= 45]) == 0,
            "note": "6 hal paling butuh perhatian hari ini (dari engine yang ada, ranked by magnitude). Sisanya collapse."}
