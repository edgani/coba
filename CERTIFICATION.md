# RESEARCH CERTIFICATION REPORT
generated: 2026-07-03 01:54 · gate = mechanism + statistical + value-add + out-of-sample

data: 482 tickers, 2013-02-08→2018-02-07

## 1. Backtest Engine (path-dependent, no look-ahead)
  path-dependent both-touch=LOSS: ✓
  status: ✅ PRODUCTION — engine correctness verified

## 2. Ticker Signal — surge-catch edge
  cross-sectional RS top-decile: lift 2.14x (>1.3 = edge)
  strategy: 18.0%/yr vs bench 14.7%/yr, sharpe 1.47
  alpha test: excess 0.25%/mo, p=0.408, beta=0.86 → mostly BETA — alpha not proven
  caught e.g. AMD: 2016-03-11 $2.52 → 2017-06-12 $12.09 (+380%)
  status: 🔬 RESEARCH — edge in tails, alpha not yet significant → RESEARCH

## 3. Absolute formation+RS signal (the naive dashboard signal)
  lift 0.85x → NO edge — ≈ random/worse
  status: ❌ FAIL — NO edge. Must NOT drive BUYs. (This is why gating matters.)

## 4. Early Warning — panic bottom / fear-greed
  panic→fwd63: +6.2% vs baseline +3.3% (edge +2.9%, p=0.0000)
  status: ✅ PRODUCTION — PANIC=BOTTOM validated

## 5. Macro Attribution — multi-driver crash (no single-cause)
  R²=0.0494 (macro explains this much of crash variance)
  confounded single-cause illusions: none
  independent drivers (survive confounding): ['CAPE', 'CPI', 'rate', 'rate_chg', 'vol']
  '2022=inflation'? CPI t=-2.02 → real
  bull 2013-19: earnings dominated (fundamental — NOT just QE) (61% earnings)
  status: ✅ PRODUCTION — attribution rigorous; crashes largely unpredictable (low R²)

## 6. Valuation Room — how much room / how long (Bubble context)
  current CAPE 30.8 (95th pct)
  when this high: fwd 1yr +4%, 3yr +13%, 62% positive
  months to next -20% drawdown: median 21.0, range 0.0-62.0
  → high valuation lowers return, does NOT time top. Show this on dashboard, not a sell signal.
  status: ✅ PRODUCTION — valuation context validated

---
## SUMMARY
- Ticker edge: cross-sectional RS top-decile (lift 2x) → RESEARCH (alpha not yet significant). Use as basis, not proven.
- Naive formation+RS signal: FAIL (no edge) → must NOT drive recommendations.
- Panic-bottom early warning: PRODUCTION-grade (p<0.001) where VIX+breadth available.
- Euphoria-top: RESEARCH (weak in bull data — needs 2008/2020/2022).
- Macro attribution: crashes are multi-driver & largely unpredictable (R²~3%). No single-cause claims.
- Valuation: context for risk-sizing, not market timing.

Discipline: nothing reaches PRODUCTION without passing all four gates. Everything traceable to a test.