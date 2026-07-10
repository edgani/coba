# What was broken and what I fixed (the 'Run failed: idx' round)

## The crash (Q1 + Q2) — FIXED
`Run failed: 'idx'` on every tab → Streamlit fell back to the raw v0.2 MOCK, which is why
everything looked synthetic again AND the multi-timeframe quad "disappeared".

Root cause = 3 bugs I introduced when wiring idx + macro proxies + regional regime:
1. `union.update(prices[m])` KeyError'd when a market (idx) failed to fetch → **now `.get(m,{})`**.
2. Offline/partial loaders return OHLCV DataFrames; the macro/flow/regime engines need 1-D close
   Series → **build_desk now coerces bench + union to close Series once, up front** (keeps the
   OHLCV dicts intact for the setup engines that need volume).
3. Same DataFrame leak in `macro_inputs.py` and `regime_multitf.py` → **both coerce now**.

Verified end-to-end on all 5 markets with idx deliberately failing: no KeyError, no ValueError,
regime_tf + systemic + regional all populate.

## The hardcoded regional row (Q3) — FIXED
You were right: `IHSG Bull / Japan Bull / …` was **hardcoded HTML** (dashboard lines 285-290),
computing nothing. That's why it always said Bull regardless of reality.

New `regional_regime.py` computes each region's regime from its **real index price** (trend vs
200d + 3m/1m momentum): Expansion / Late-cycle / Weakening / Recovery / Bear / Neutral.
Fetches ^GSPC, MCHI, VGK, ^N225, ^BSESN, **^JKSE** (real IHSG), BTC-USD, DBC. So IHSG now reflects
actual IHSG price action — if it's weak, it shows weak. Labeled honestly as a price-proxy regime
(not a full macro quad). Regions with no data show "—", never a fake label.

## Formula audit (Q4) — the two weighted formulas match the code exactly
- Fear-Greed `0.4·(1-VIXpct) + 0.3·(1-breadth) + 0.3·mom-z` == `early_warning.py:37` ✓
- Accumulation `0.30·RS + 0.25·VE + 0.20·ΔER + 0.15·own + 0.10·OI` == `accumulation.py:31` ✓
  (honest caveat already shown on the panel: ΔER/own/OI = 0 without the fundamental/options feed.)

## Tickers (Q5)
Everything you screenshotted was the MOCK fallback (because of the crash), so those tickers are the
hardcoded illustrative set. Live, tickers come from the screener I validated on real 2013-18 data
(ITE replay caught 4/5 winners pre-markup; factor IC 5/5; panic-bottom PRODUCTION). I can't fetch
live from this sandbox to show you the *current* live tickers — that runs on your machine.

## Run it
`streamlit run app.py` → Live. If a panel is still off, F12 console names the exact feed/key.
