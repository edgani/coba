"""run.py — War Room OS end-to-end runner (gcfis orchestrator = brain, one pipeline).

Drop this + data_layer.py + dashboard.html into your warroom_pro_full root (next to gcfis/),
then:

    pip install -r requirements.txt          # yfinance, statsmodels, hmmlearn, etc.
    python run.py                            # live data on your machine → desk_data.json + dashboard.html
    python run.py --synthetic                # offline: proves the pipeline runs (no fabricated edge)
    python run.py --markets us,crypto        # subset

Output:
    desk_data.json   — structured desk (systemic macro + per-market setups + asymmetric alpha)
    dashboard.html   — the approved v0.3 UI, POPULATED with the run (open in a browser)

HONEST: setups only appear where the conviction gate is met. On synthetic/noise data that is
often zero rows — that is correct behavior (the gate refuses to fabricate). Edge is only real
where run_validation.py --cache clears perm_p<0.05 AND DSR>=0.95 on YOUR data.
"""
from __future__ import annotations
import os, sys, json, argparse, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)          # data_layer.py + gcfis/ live here
import data_layer as DL

from gcfis.orchestrator import run_gcfis
from gcfis.markets import market_of, is_long_only, MARKETS
from gcfis.engines.entry import run_entry
from gcfis.engines.asymmetric_discovery import run_discovery
from gcfis.market_drivers import read_all as market_bias


def _num(x, d=None):
    try:
        f = float(x)
        return round(f, 3)
    except Exception:
        return d


def _setup_from_ranking(entry, price, direction):
    """Enrich a ranking row (ticker/action/conviction/reason) with entry/stop/target via entry.py."""
    tk = entry.get("ticker")
    lo = is_long_only(tk)
    e = run_entry(price, direction, long_only=lo) if price is not None and len(price) > 60 else {}
    return {
        "tk": tk, "act": entry.get("action", ""), "dir": direction,
        "conv": _num(entry.get("conviction"), 0),
        "e": _num(e.get("entry_px"), None), "s": _num(e.get("stop"), None),
        "t": _num(e.get("target"), None), "rr": _num(e.get("rr"), None),
        "ty": e.get("entry_type", ""), "gm": e.get("gamma_regime", ""),
        "valid": bool(e.get("valid", False)), "warn": e.get("warning", ""),
        "why": entry.get("reason", ""),
    }


def build_desk(data, top_per_market=12):
    prices, bench = data["prices"], data["bench"]
    union = {}
    for m in data["markets"]:
        union.update(prices[m])
    if bench is None or not union:
        raise SystemExit("no price data (need bench + universe). On your machine: pip install yfinance.")

    out = run_gcfis(union, bench, regime_posterior={"chop": 1.0})
    rk = out.get("ranking", {})
    sysm = out.get("systemic", {})

    # ── systemic macro (Mission Control + Macro tab) ──
    fm = sysm.get("forward_macro", {}) or {}
    liq = sysm.get("liquidity", {}) or {}
    fr = sysm.get("fragility", {}) or {}
    sh = sysm.get("shock", {}) or {}
    xa = sysm.get("cross_asset", {}) or {}
    fl = sysm.get("flow", {}) or {}
    systemic = {
        "quad": fm.get("forward_quad"), "quad_name": fm.get("quad_name"),
        "growth_roc": _num(fm.get("GROC")), "infl_roc": _num(fm.get("IROC")),
        "liquidity": liq.get("reason") or ("expanding" if liq.get("expanding") else "—"),
        "fragility": _num(fr.get("fragility")) if fr.get("ok") else fr.get("reason"),
        "shock_prob": _num(sh.get("shock_prob")) if sh.get("ok") else sh.get("reason"),
        "cross_asset": xa.get("regime"), "defer_longs": xa.get("defer_longs"),
        "rotation_in": fl.get("rotating_in", []), "rotation_out": fl.get("rotating_out", []),
    }

    # ── per-market setups (group ranking by market) ──
    long_rows = rk.get("master_long", [])
    short_rows = rk.get("master_short", [])
    spot_rows = rk.get("master_spot", [])
    eliminated = {e.get("ticker"): e.get("reason", "eliminated") for e in rk.get("eliminated", []) if isinstance(e, dict)}
    bias = market_bias(None)  # driver matrix map (readings None without feeds → honest)

    markets = {}
    for m in data["markets"]:
        univ = list(prices[m].keys())
        setups = []
        for row in long_rows:
            if market_of(row.get("ticker")) == m:
                setups.append(_setup_from_ranking(row, prices[m].get(row["ticker"]), "long"))
        for row in short_rows:
            if market_of(row.get("ticker")) == m and not MARKETS[m]["long_only"]:
                setups.append(_setup_from_ranking(row, prices[m].get(row["ticker"]), "short"))
        for row in spot_rows:
            if market_of(row.get("ticker")) == m:
                s = _setup_from_ranking(row, prices[m].get(row["ticker"]), "long")
                s["ty"] = s["ty"] or "SPOT"
                setups.append(s)
        setups = setups[:top_per_market]
        drv = bias.get("gold" if m == "commodity" else m, {})
        markets[m] = {
            "label": MARKETS[m]["label"], "long_only": MARKETS[m]["long_only"],
            "drivers": MARKETS[m]["drivers"],
            "bias": drv.get("bias", "NO_DATA"),
            "funnel": {"universe": len(univ),
                       "eliminated": sum(1 for t in univ if t in eliminated),
                       "setups": len(setups)},
            "setups": setups,
        }

    # ── asymmetric alpha (Alpha tab) — structural, over the moonshot universe ──
    disc = run_discovery(top=20)
    alpha = [{
        "tk": c["ticker"], "market": c["domain"], "asymmetry": c["asymmetry"],
        "tier": c["tier"], "upside": c["upside_bucket"], "base_rate": c["base_rate"],
        "stage": c["stage"], "node": c["node"], "scarcity": c["scarcity"],
        "gated": c.get("feed_gated_neutral", []),
    } for c in disc["candidates"][:12]]

    return {
        "meta": {
            "generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "source": data["overall_source"],
            "sources": data["sources"], "fred_source": data["fred_source"],
            "universe_n": len(union),
            "note": disc["summary"].get("note", ""),
        },
        "systemic": systemic,
        "markets": markets,
        "alpha": alpha,
        "desk_picks": out.get("final_desk", {}),
    }


def render_dashboard(desk, template_path, out_path):
    """Inject desk JSON into the approved dashboard template (self-contained HTML)."""
    if not os.path.exists(template_path):
        sys.stderr.write(f"[run] template {template_path} not found — skipping HTML render\n")
        return False
    html = open(template_path, encoding="utf-8").read()
    payload = "window.DASHBOARD_DATA = " + json.dumps(desk) + ";"
    if "/*__INJECT_DATA__*/" in html:
        html = html.replace("/*__INJECT_DATA__*/", payload)
    else:  # inject right after <body>
        html = html.replace("<body>", "<body>\n<script>" + payload + "</script>", 1)
    open(out_path, "w", encoding="utf-8").write(html)
    return True


def print_summary(desk):
    m = desk["meta"]; s = desk["systemic"]
    print(f"\n{'='*66}\nWAR ROOM OS — run @ {m['generated']}  [{m['source']}]  universe={m['universe_n']}")
    print(f"{'='*66}")
    print(f"MACRO: quad={s['quad']} ({s['quad_name']}) | liquidity={s['liquidity']} | "
          f"fragility={s['fragility']} | shock={s['shock_prob']} | x-asset={s['cross_asset']}")
    total = sum(len(mk["setups"]) for mk in desk["markets"].values())
    print(f"\nPER-MARKET SETUPS (convicted only — empty = gate not met, not a bug):")
    for mid, mk in desk["markets"].items():
        f = mk["funnel"]
        print(f"  {mk['label']:12} universe {f['universe']:>2} → eliminated {f['eliminated']:>2} → "
              f"setups {f['setups']:>2}   bias={mk['bias']}")
        for x in mk["setups"][:6]:
            rr = f"R/R {x['rr']}" if x["rr"] else "—"
            flag = "" if x["valid"] else " [INVALID: " + (x["warn"] or "gate") + "]"
            print(f"      {x['tk']:10} {x['act']:13} conv={x['conv']:<5} {x['ty']:12} {rr}{flag}")
    print(f"\n  TOTAL convicted setups: {total}")
    print(f"\nASYMMETRIC ALPHA (structural, top {len(desk['alpha'])}):")
    for a in desk["alpha"][:8]:
        g = " (feed-gated: " + ",".join(a["gated"]) + ")" if a["gated"] else ""
        print(f"  {a['tk']:8} asym={a['asymmetry']:<5} tier{a['tier']} {a['upside']:<8} "
              f"[{a['base_rate']}] {a['node'][:40]}{g}")
    print(f"\nRULE: act only where run_validation.py --cache clears perm_p<0.05 AND DSR>=0.95 on YOUR data.\n")


def main():
    ap = argparse.ArgumentParser(description="War Room OS runner")
    ap.add_argument("--synthetic", action="store_true", help="force offline synthetic (no live fetch)")
    ap.add_argument("--markets", default=None, help="comma list, e.g. us,crypto,fx")
    ap.add_argument("--start", default="2022-01-01")
    ap.add_argument("--out", default=os.path.join(HERE, "desk_data.json"))
    ap.add_argument("--template", default=os.path.join(HERE, "dashboard.html"))
    ap.add_argument("--html", default=os.path.join(HERE, "dashboard_live.html"))
    args = ap.parse_args()

    markets = args.markets.split(",") if args.markets else None
    data = DL.load_all(markets=markets, start=args.start, allow_live=not args.synthetic)
    desk = build_desk(data)

    json.dump(desk, open(args.out, "w"), indent=2, default=str)
    rendered = render_dashboard(desk, args.template, args.html)
    print_summary(desk)
    print(f"→ desk_data.json written: {args.out}")
    if rendered:
        print(f"→ dashboard written:      {args.html}  (open in a browser)")


if __name__ == "__main__":
    main()
