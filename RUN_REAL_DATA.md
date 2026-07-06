# How to make REAL data load (why you're seeing mock, and the fix)

## Why the screenshots show mock / NVDA 182 / "needs FRED"

1. **NVDA 182, fear-greed 58, "needs FRED", "MOCK"** = hardcoded illustrative values in `dashboard.html`.
   They are placeholders, replaced only when a real run is injected.
2. **NVDA 182 is not wrong — it's the real 2018 price** from the bundled historical panel. It is NOT today's
   price because the panel ends 2018-02 and this environment cannot fetch live data.
3. **On Streamlit Cloud, yfinance gets rate-limited from datacenter IPs** → your loader silently falls back
   to synthetic → you see mock. This is the #1 reason "the data doesn't load" on a cloud deploy.

## The fix — build the cache locally, commit it (10 minutes)

Yahoo works from YOUR home IP, not from cloud. So fetch once locally, commit the result, let Cloud read it.

```bash
# 1) on YOUR machine (not the cloud):
pip install -r requirements.txt
python build_cache.py --full          # yf.download your 207-name universe → cache/prices.parquet
                                       # verify it printed real tickers + a recent date

# 2) commit the cache so the cloud app can read it:
git add cache/prices.parquet
git commit -m "real price cache"
git push                               # redeploy picks it up

# 3) FRED (liquidity/fragility/shock): fredgraph (no key) usually works on cloud, but for reliability:
#    Streamlit Cloud → your app → Settings → Secrets:  FRED_API_KEY = "your_free_key"
```

After this, open the app: the green banner shows **"✓ Local price cache found — N tickers, latest <date>"**,
pick **Live**, and the header badge flips to **REAL DATA / LIVE** — NVDA shows today's price, fear-greed from
real VIX, liquidity from real FRED. No mock.

## If you can't build a cache

Pick **Real S&P history (2013-18)** — it runs the engines on the bundled REAL panel (not synthetic):
real US tickers, real setups, real macro. Prices are 2018-era (real, just not current). The badge says
**REAL DATA**, not MOCK.

## How to run the validation tests (and what results to expect)

```bash
python validate_all.py     # runs all 7 suites on the bundled REAL data (no feeds needed)
```
Expected (see TEST_REPORT.md for the full table):
- validator controls → **VALIDATOR VALIDATED** (noise→NOISE, planted→TRADEABLE)
- factor IC → **reproduces your factor_ic.parquet 5/5 exactly**
- panic-bottom (real VIX) → **+6.6% vs +3.2%, p<0.0001**  ← strongest live edge
- every engine → **21 PASS / 0 FAIL**
- alpha discovery (NVDA test) → **price/volume FAILS (IC −0.12)** — needs structural feeds (honest)

If any suite errors on your machine, paste the traceback — that's the only thing I can't reproduce here
(this sandbox blocks the network, so I validate on the bundled real historical data instead of live).
