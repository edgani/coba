"""run_research.py — reproduces the multi-driver attribution & ticker validation on REAL data.

Usage:
  python run_research.py --macro                    # crash/bull attribution (Shiller+VIX in research/)
  python run_research.py --tickers PANEL.parquet    # walk-forward + IC on your OHLC panel
  python run_research.py --all                       # both, using bundled research/ data

Panel format for --tickers: parquet with columns [date, open, high, low, close, volume, Name]
(the same shape as research/sp500_panel.parquet). Point it at your own cache for multi-regime results.

Nothing here fabricates: if data is missing it says so and skips. Results are printed + saved to
research/. This is the honest engine — feed it your data, read the verdicts.
"""
from __future__ import annotations
import sys, os, argparse
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _frame(g):
    g = g.sort_values("date").set_index("date")
    return g.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"})[
        ["Open", "High", "Low", "Close", "Volume"]]


def tickers(panel_path):
    from warroom import backtest as BT
    print(f"\n{'='*70}\nTICKER VALIDATION — walk-forward + bootstrap on real data\n{'='*70}")
    if not os.path.exists(panel_path):
        print(f"  panel not found: {panel_path}"); return
    panel = pd.read_parquet(panel_path)
    px = {t: _frame(g) for t, g in panel.groupby("Name") if len(g) >= 300}
    print(f"universe: {len(px)} tickers, {panel.date.min().date()}→{panel.date.max().date()}")
    allc = pd.DataFrame({t: d["Close"] for t, d in px.items()}).dropna(how="all")
    bench_rs = (((1 + allc.pct_change().mean(axis=1)).cumprod()) / ((1 + allc.pct_change().mean(axis=1)).cumprod()).shift(63) - 1)

    def make_sig(t):
        def sig(h):
            c = h["Close"]
            if len(c) < 70: return False
            if not (c.tail(20).mean() > c.tail(50).mean() and c.iloc[-1] > c.tail(50).mean()): return False
            r63 = c.iloc[-1] / c.iloc[-64] - 1; b = bench_rs.get(c.index[-1], 0.0)
            return (r63 - (b if b == b else 0)) > 0
        return sig

    def lvl(h, d):
        p = float(h["Close"].iloc[-1]); return p, p * 0.94, p * 1.10

    rows = []
    for t, d in px.items():
        bt = BT.backtest_rule(d, make_sig(t), lambda h: "Long", lvl, warmup=80, max_bars=21, cost_bps=10)
        s = bt["stats"]
        if s.get("n_closed", 0) >= 10:
            boot = BT.bootstrap_pvalue(d, bt["trades"], n_boot=150)
            rows.append({"ticker": t, "n_closed": s["n_closed"], "hit": s["hit_rate"],
                         "exp_pct": s["expectancy_pct"], "pf": s["profit_factor"], "boot_p": boot.get("p_value")})
    R = pd.DataFrame(rows)
    if R.empty:
        print("  no names with >=10 closed trades"); return
    R["PASS"] = (R.exp_pct > 0) & (R.hit > 0.50) & (R.boot_p < 0.10) & (R.n_closed >= 10)
    R = R.sort_values(["PASS", "exp_pct"], ascending=[False, False])
    print(f"\nVALIDATED (exp>0, hit>50%, beats-random p<0.10, n>=10): {int(R.PASS.sum())}/{len(R)}")
    print(R.head(15).to_string(index=False))
    R.to_parquet("research/ticker_validation_out.parquet")
    print("\n→ saved research/ticker_validation_out.parquet")
    if R.PASS.sum() == 0:
        print("\n⚠ 0 PASS — the simple momentum signal has no proven edge on this data. Do NOT surface these")
        print("  as BUYs. This is the discipline: production is earned, not assumed.")


def macro():
    from warroom import causal_attribution as CA
    print(f"\n{'='*70}\nMACRO ATTRIBUTION — multi-driver crash & bull decomposition\n{'='*70}")
    sh = "research/shiller.csv"; vx = "research/vix.csv"
    if not os.path.exists(sh):
        print(f"  {sh} not found — download Shiller data or point to yours"); return
    s = pd.read_csv(sh, parse_dates=["Date"]).set_index("Date").sort_index()
    s = s[s["Consumer Price Index"] > 0].copy()
    s["cpi_yoy"] = s["Consumer Price Index"].pct_change(12) * 100
    s["rate"] = s["Long Interest Rate"]; s["rate_chg"] = s["rate"].diff(12)
    s["ret"] = s["SP500"].pct_change(); s["vol12"] = s["ret"].rolling(12).std() * np.sqrt(12)
    s["cape"] = s["PE10"]
    vals = s["SP500"].values
    s["fwd_dd12"] = [(np.min(vals[i:i + 13]) / vals[i] - 1) if i + 1 < len(vals) else np.nan for i in range(len(s))]
    df = s.dropna(subset=["cape", "cpi_yoy", "rate", "rate_chg", "vol12", "fwd_dd12"])

    print(f"\nsample: {len(df)} months ({df.index.min().date()}→{df.index.max().date()})")
    res = CA.univariate_vs_multivariate(df["fwd_dd12"].values,
        {"CAPE": df["cape"].values, "CPI_YoY": df["cpi_yoy"].values, "rate_level": df["rate"].values,
         "rate_change": df["rate_chg"].values, "prior_vol": df["vol12"].values})
    print(f"\nR² = {res['r2']} (macro factors explain this fraction of drawdown variance)\n")
    print(f"{'factor':<14}{'uni_corr':>10}{'uni_p':>8}   {'multi_t':>8}  independent driver?")
    for nm in res["univariate"]:
        u = res["univariate"][nm]; m = res["multivariate"].get(nm, {})
        print(f"{nm:<14}{u['corr']:>10}{u['p']:>8}   {m.get('t_stat',0):>8}  {m.get('independent_driver')}")
    print(f"\nconfounded single-cause illusions: {res['confounded_illusions']}")
    print(f"→ {res['note']}")

    print(f"\n{'-'*50}\nBULL-RUN DECOMPOSITION (earnings vs multiple)\n{'-'*50}")
    for label, lo, hi in [("2013-2019 (QE era)", "2013-01", "2019-12"), ("2020-2021 (stimulus)", "2020-04", "2021-12")]:
        seg = s.loc[lo:hi]
        if len(seg) < 2: continue
        d = CA.return_decomposition(seg["SP500"].iloc[0], seg["SP500"].iloc[-1],
                                    seg["Earnings"].iloc[0], seg["Earnings"].iloc[-1],
                                    seg["PE10"].iloc[0], seg["PE10"].iloc[-1])
        if d:
            print(f"  {label}: +{d['total_return_pct']}% | earnings {d['earnings_growth_pct']:+}% · "
                  f"multiple {d['multiple_expansion_pct']:+}% → {d['verdict']}")
    print("\n→ Full write-up: research/RESEARCH_FINDINGS.md")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--macro", action="store_true")
    ap.add_argument("--tickers", metavar="PANEL.parquet")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    if a.all or a.macro:
        macro()
    if a.all:
        tickers("research/sp500_panel.parquet")
    elif a.tickers:
        tickers(a.tickers)
    if not (a.macro or a.tickers or a.all):
        ap.print_help()


if __name__ == "__main__":
    main()
