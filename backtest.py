"""wr/backtest.py — walk-forward + bootstrap (lean). No look-ahead, path-dependent, honest p-values.

Ini fondasi disiplin: "production is earned". Sinyal ga lolos gate → ga jadi rekomendasi.
"""
from __future__ import annotations
import numpy as np
import pandas as pd


def simulate_trade(df, entry_i, direction, entry, stop, target, max_bars=21, cost_bps=10):
    """Path-dependent single trade. Both-touch in a bar = conservative LOSS."""
    c = df["Close"].values; h = df["High"].values; lo = df["Low"].values
    cost = cost_bps / 10000.0
    for j in range(entry_i + 1, min(entry_i + 1 + max_bars, len(df))):
        if direction == "Long":
            hit_stop = lo[j] <= stop; hit_tgt = h[j] >= target
            if hit_stop and hit_tgt:
                return {"outcome": "LOSS", "ret": (stop / entry - 1) - cost}
            if hit_stop:
                return {"outcome": "LOSS", "ret": (stop / entry - 1) - cost}
            if hit_tgt:
                return {"outcome": "WIN", "ret": (target / entry - 1) - cost}
        else:
            hit_stop = h[j] >= stop; hit_tgt = lo[j] <= target
            if hit_stop and hit_tgt:
                return {"outcome": "LOSS", "ret": (entry / stop - 1) - cost}
            if hit_stop:
                return {"outcome": "LOSS", "ret": (entry / stop - 1) - cost}
            if hit_tgt:
                return {"outcome": "WIN", "ret": (entry / target - 1) - cost}
    j = min(entry_i + max_bars, len(df) - 1)
    r = (c[j] / entry - 1) if direction == "Long" else (entry / c[j] - 1)
    return {"outcome": "FLAT", "ret": r - cost}


def backtest_signal(df, signal_fn, direction_fn, level_fn, warmup=80, max_bars=21, cost_bps=10):
    """Run a signal over history. signal_fn(hist)->bool, direction_fn(hist)->'Long'/'Short', level_fn(hist)->(entry,stop,target)."""
    trades = []
    i = warmup
    while i < len(df) - 1:
        hist = df.iloc[:i + 1]
        if signal_fn(hist):
            direction = direction_fn(hist)
            entry, stop, target = level_fn(hist)
            t = simulate_trade(df, i, direction, entry, stop, target, max_bars, cost_bps)
            trades.append(t)
            i += max_bars  # no overlapping
        else:
            i += 1
    rets = [t["ret"] for t in trades]
    if not rets:
        return {"stats": {"n": 0}, "trades": []}
    rets = np.array(rets)
    wins = (rets > 0).sum()
    stats = {"n": len(rets), "n_closed": len(rets), "hit_rate": wins / len(rets),
             "expectancy_pct": rets.mean() * 100, "total_ret_pct": ((1 + rets).prod() - 1) * 100,
             "profit_factor": (rets[rets > 0].sum() / -rets[rets < 0].sum()) if (rets < 0).any() and rets[rets < 0].sum() != 0 else float("inf"),
             "max_dd_pct": _maxdd(rets) * 100}
    return {"stats": stats, "trades": trades, "returns": rets}


def _maxdd(rets):
    eq = np.cumprod(1 + rets)
    peak = np.maximum.accumulate(eq)
    return float(((eq - peak) / peak).min())


def bootstrap_pvalue(df, trades, n_boot=200, max_bars=21):
    """Compare strategy expectancy vs random-entry trades of the same count. Returns p-value."""
    if not trades or len(trades) < 8:
        return {"p_value": 1.0, "note": "too few trades"}
    actual = np.mean([t["ret"] for t in trades])
    c = df["Close"].values
    n = len(trades)
    rng = np.random.default_rng(0)
    boot = []
    for _ in range(n_boot):
        idxs = rng.integers(80, len(df) - max_bars - 1, n)
        rr = []
        for ii in idxs:
            fwd = c[min(ii + max_bars, len(c) - 1)] / c[ii] - 1
            rr.append(fwd)
        boot.append(np.mean(rr))
    boot = np.array(boot)
    p = (boot >= actual).mean()
    return {"p_value": float(p), "actual_exp": float(actual), "random_exp": float(boot.mean())}


def rs_top_decile_signal(close, lookback=126, decile=0.90):
    """The ONE tested ticker signal: cross-sectional relative-strength top-decile membership (lift 2x)."""
    dret = close.pct_change().fillna(0)
    ew = (1 + dret.mean(axis=1)).cumprod()
    rs = (close / close.shift(lookback) - 1).sub((ew / ew.shift(lookback) - 1), axis=0)
    return rs.rank(axis=1, pct=True) > decile


def surge_lift(close, signal_matrix, surge=0.30, horizon=63):
    """LIFT = P(surge | signal) / P(surge | random). >1.3 = edge."""
    fwd = close.shift(-horizon) / close - 1
    base = (fwd >= surge).sum().sum() / max(1, fwd.notna().sum().sum())
    turns = signal_matrix & ~signal_matrix.shift(1).fillna(False)
    hits = tot = 0
    for t in close.columns:
        for dt in turns[t][turns[t]].index:
            loc = close.index.get_loc(dt)
            if loc < len(close) - horizon:
                c0 = close[t].iloc[loc]
                if pd.notna(c0):
                    tot += 1; hits += int(close[t].iloc[loc + horizon] / c0 - 1 >= surge)
    if tot < 20:
        return {"lift": None, "note": "too few fires"}
    p = hits / tot
    return {"lift": round(p / base, 2) if base else None, "hit_rate": round(p, 4), "base": round(base, 4), "fires": tot}
