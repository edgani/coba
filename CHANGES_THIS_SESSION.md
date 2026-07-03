# War Room — Perubahan (sesi ini)

Verdict dulu: **approach entry/stop/target lama udah gw ganti total, gw nemu 1 bug parah (gatekeeper
random), gw benerin, dan gw bangun test suite yang jujur.** Detail:

---

## A. DECISION APPROACH — DIGANTI (sesuai spec dokumen IIDOS lu)

**Yang lama (dibuang):**
- `stop = px * 0.97`, `target = px * 1.06` — hardcoded, ga ada hubungannya sama struktur.
- Entry zone yang **lower bound-nya = stop** → kalau fill di bawah zona, langsung stopped out. (terbukti di audit: `entry='141.37–145.74' stop=141.37`)
- `optimal_entry._rr` fallback fabrikasi level ±3% kalau risk range gagal.
- `render._asymmetry` P(win) = `0.40 + 0.35*score/100` — **angka dikarang dari score, dilabel "est"** tapi tetep muncul ke user.
- `analyze_watchlist` direction dari `close>=sma50` doang (beda dari `_rank` yang pakai formation+RS).

**Yang baru (`warroom/decision_center.py`, LEVEL 8):**
- **ENTRY**: 3 zona (Conservative/Base/Aggressive) + DCA ladder + pyramid level — **semua diturunkan dari Hedgeye TRADE/TREND band**. Ga ada risk range → level **di-withhold + flag**, TIDAK difabrikasi.
- **5 STOP**: Technical (band-derived), Macro (kondisi quad-flip), Thesis (kill-switch kausal dari chain), Time (10-bar no follow-through), Fundamental (cuma kalau feed ada; kalau ga: *"absent, not faked"*).
- **TARGET**: T1=TRADE opposite · T2=TREND · T3=TAIL, dengan sanitasi — kalau T2/T3 jatuh di dalam T1 (kejadian di beberapa vol-state), rung-nya **di-drop**, bukan bikin ladder ngaco.
- **P(win)/EV**: **calibrated-or-silent** — cuma tampil kalau ada ≥30 closed trade di tracker DB. Di bawah itu → `"uncalibrated — baru N closed"`, EV ga ditampilkan. **Nol fabrikasi.**
- **INVALIDATION**: daftar kondisi kausal yang bisa diuji (bukan cuma level harga).
- **REKOMENDASI**: BUY/WATCH/AVOID/SELL/HOLD (vocab spec), aturan eksplisit & bisa diaudit.

Semua parameter struktur (0.5·half stop, rung DCA, 10-bar) **dilabel PRIOR TAK-TERVALIDASI** dan masuk daftar uji di `run_validation.py` (stability phase).

**Wiring**: `compute.py` nyimpen `_rr_full` di tiap setup + panggil `DC.build()` di loop `_tag` untuk conviction & semua market setups. `render._asymmetry` sekarang baca `decision_pkg`.

---

## B. BUG PARAH — GATEKEEPER PALSU (ini yang lu minta gw cari)

`engines/walkforward_backtest_engine.batch_gatekeeper()` — yang **ke-wire ke dashboard lu sebagai
"Walk-forward + MC 100x Gatekeeper"** — isinya:

```python
wf_score = random.uniform(50, 85)
mc_score = random.uniform(55, 90)
gate_status = "PASS" if combined >= 55 else "FAIL"
optimal_stop_adj = round(random.uniform(-2, 0), 1)
```

**Semua PASS/FAIL, skor validasi, "optimal stop adjustment" yang lu liat = angka acak.** Tiap refresh
beda. Gw buktiin: call 1 = 66.3, call 2 = 62.7, dari input yang sama persis.

**Fix**: gw bangun `warroom/backtest.py` — walk-forward **beneran**:
- Path-dependent trade sim (telusuri OHLC ke depan, WIN/LOSS dari mana yang kena duluan; both-touch = LOSS konservatif, sama kayak tracker).
- **No look-ahead** (sinyal bar t cuma diuji di bar > t — terbukti: max hist_len ≤ n).
- Walk-forward folds kronologis (IS/OOS terpisah).
- Block-bootstrap p-value (block=5) vs entry acak.
- Net-of-cost (bps).
- `batch_gatekeeper_real()` = drop-in replacement. PASS butuh: ≥15 closed, hit>52%, expectancy>0, **beats random (p<0.10)**.

`compute.py` sekarang manggil yang REAL. Yang lama gw karantina (masih ada di engines/ tapi ga dipanggil).

---

## C. TEST SUITE (jawaban "run semua test")

`run_validation.py` — subset yang **beneran bisa dijalankan** dari ~200-test framework lu (attachment 1-3):

```
python run_validation.py --synthetic   # sandbox: buktiin mesin jalan & ga look-ahead
python run_validation.py --cache        # mesin lu: verdict beneran (butuh build_cache.py dulu)
```

Tiap test statusnya: **PASS/FAIL** (dijalankan) · **NEEDS-DATA** (butuh data real/vintage/feed) ·
**NEEDS-TIME** (butuh calendar time buat track record). **Ga ada verdict yang dikarang.**

Hasil synthetic run: **15 PASS, 0 FAIL, 18 NEEDS-DATA/TIME**. Yang PASS antara lain:
- quad sign-mapping (G/I → Q1-4) benar
- deteksi gatekeeper palsu
- no fabricated levels
- P(win) not score-mapped
- path-dependent both-touch=LOSS
- no look-ahead
- walk-forward folds jalan
- block-bootstrap discriminates
- parameter stability across window
- meta-validation (deflated t-stat guard ada)

**Kenapa banyak NEEDS-DATA**: test kayak regime-robustness (2006-2026), COT edge, counterfactual,
decision-impact ladder, capacity/execution — semua butuh data harga REAL + feed + vintage FRED yang
**ke-block di sandbox** (yahoo/fred/stooq semua 403). Gw ga mau pura-pura. Jalanin `--cache` di mesin
lu abis `build_cache.py` + `build_feeds.py`, phase-phase itu langsung aktif.

---

## D. DASHBOARD — AMBIL DARI REFERENSI (yang lu kirim)

Dari dashboard Nova Capital/bimagalih6_ yang lu attach, gw ambil **layout country-regime grid** (Image 6)
karena emang bersih & gampang dibaca. Tapi:

**`warroom/country_regime.py`** — grid 16 negara Goldilocks/Reflation/Stagflation/Deflation, TAPI tiap
label **dihitung dari price-proxy quad beneran** (growth = momentum ETF negara 63d-126d, inflation =
commodity tilt global), **bukan label karangan**. Negara tanpa proxy → **"data pending"**, bukan regime palsu.

**Keterbatasan yang gw akui**: inflation axis masih **shared** (satu commodity proxy global) — jadi
`i` sama buat semua negara sampai lu wire CPI per-negara. Growth axis udah beda-beda. Ini gw tulis di
`note` field yang muncul di UI, ga gw sembunyiin. Ke-render di Command Center abis Quad path.

Yang **ga** gw ambil dari referensi: mereka ga punya decision layer, entry/stop/target, validation,
causal chains. Itu punya lu udah lebih jauh. Jadi gw ambil presentasi, bukan logika.

---

## Yang HARUS lu lakuin di mesin sendiri

1. `python build_cache.py` → tarik harga real ke parquet.
2. `export FRED_API_KEY=... && python build_feeds.py` → FRED + COT + Type-F + on-chain.
3. `python run_validation.py --cache` → **sekarang verdict-nya beneran.** Baca `validation_report.json`.
4. Track record (P(win) kalibrasi) **akrual seiring waktu** — tiap hari lu buka app, `tracker.py` log
   sinyal point-in-time + resolve yang lama. Setelah ~30 closed trade per bucket, P(win) mulai muncul.

Yang **ga bisa** gw kasih dari sini: angka backtest "final" atas data real, karena datanya ke-block.
Mesin-nya udah bener & terbukti ga look-ahead — tinggal kasih makan data lu.

---

# LANJUTAN (turn ini) — Market-Cap Target, Convexity, Decision Market

Verdict: dari tiga hal yang lu tunjuk, **#1 (target/stop dari market cap) — SELESAI & teruji.** #2 (ticker)
dan #3 (UI/UX) — gw jelasin jujur di bawah mana yang beres, mana yang butuh effort terpisah + kenapa.

## #1 — TARGET DARI MARKET CAP + CONVEXITY (SELESAI)

`warroom/market_cap_target.py` — ini jawaban langsung pertanyaan lu di dokumen: **target JANGAN cuma
teknikal (TREND high). Target = expected market cap.**

Alurnya (persis blueprint lu — Company = kendaraan, bukan endpoint):
```
Company → Expected Market Cap (bull/base/bear) → Price Target → Convexity → Portfolio Weight
```

- **Target harga** = dari expected market cap: `price_target = price × (mcap_target/mcap_now) × (1−dilution)`.
- **Scale by ukuran** (inti beta-chain): nama $3B punya room 10x lebih besar dari $131B. OKLO $3.1B →
  +319% GENERATIONAL; GEV $131B → +132% STRATEGIC. Thesis sama, convexity beda per market cap.
- **Convexity**: upside/downside, EV (probability-weighted), max permanent loss, tail ratio, flag asimetris.
- **Alpha DIPISAH** (permintaan eksplisit lu): TACTICAL &lt;20% · STRATEGIC 20-80% · GENERATIONAL 10x+.
- **Kill-thesis** ("what would change my mind"): kondisi kausal yg mematikan thesis, per thesis (dari dokumen lu).
- **Suggested weight**: EV × conviction, di-cap. Expected market cap → portfolio weight.

Thesis TAM table (`_THESIS`): ai_power / ai_compute / photonics / uranium / crypto_beta + generic.
Multiples & probabilitas = **PRIOR yang bisa lu kalibrasi**, bukan presisi karangan. Ada di 1 tempat,
gampang di-edit.

**Wiring**: `decision_center.build` sekarang manggil MC engine (market cap dari `fair_value` yfinance).
Tiap ticker card nampilin DUA target: *tactical* (risk-range, buat eksekusi/exit) + *thesis* (expected
market cap, 18-30 bulan). Beda horizon, dua-duanya kepake.

## DECISION MARKET (SELESAI)

`market_cap_target.decision_market()` + `render.decision_market_panel()` — spec "Decision Market" lu:
bukan "Buy Bloom", tapi **efficient frontier** antar kandidat dalam satu thesis:
- Semua kandidat di-rank by EV, tiap satu ada bull/bear target + tail + alpha tier + size.
- **Frontier**: MAX-EV / MIN-RISK / MAX-CONVEXITY — masing-masing beda nama + trade-off-nya.
- Muncul di tab **Alpha Center**, grouped per thesis.

## #2 — TICKER UNIVERSE (sebagian; jujur)

Universe di `data.py` udah center di thesis lu: AI compute (NVDA/AMD/AVGO/MRVL), power (VRT/GEV/CEG/VST/
BE/OKLO), photonics (COHR/LITE/FN), uranium (CCJ/UEC/DNN/NXE), materials (MP/ATI/MTRN/KTOS), crypto beta
(BTC→ETH→SOL + miners). Beta-play chains ada di `beta_play.py`.

**Yang gw ubah**: nambah country-proxy ETF (buat grid). **Yang BELUM**: ranking masih murni momentum
(RS/formation), jadi kadang ETF broad (XLU/XLP) naik ke conviction. Kalau lu mau conviction **selalu**
thesis-name (bukan ETF), itu keputusan desain — bilang, gw kasih thesis-membership boost di ranking.
Sekarang gw ga maksa itu karena bisa jadi overfitting ke preferensi. Decision Market udah nyusun per
thesis, jadi struktur beta-chain-nya kejawab di situ.

## #3 — UI/UX (country grid SELESAI; overhaul penuh = effort terpisah, ini alasannya)

Dari screenshot lu (Nova Capital), gw udah ambil + bangun **country regime grid** (16 negara,
price-proxy quad beneran). Komponen lain di screenshot lu: Economic Surprise Index, cross-country Bond
Yields table, Market Catalyst cards, COT positioning gauge, Reddit sentiment.

**Kenapa gw ga overhaul semua sekarang**, jujur:
1. **Feed ke-block di sandbox.** Economic surprise, bond yields multi-negara, COT — semua butuh feed
   (FRED/CFTC/dll) yang 403 di sini. Gw bisa bangun renderer-nya, tapi ga bisa nge-render pake data real
   buat lu verifikasi. Bikin UI cantik yang isinya kosong/synthetic = melanggar prinsip lu sendiri.
2. **render.py 1364 baris** HTML/CSS yang udah kebangun. Overhaul dari 0 dalam satu turn = risiko besar
   mecahin banyak hal yang udah jalan. Lebih aman incremental.
3. **Scope.** Pixel-match 17 tab ke aesthetic Nova = multi-sesi. Gw ga mau over-promise.

**Rekomendasi gw** buat UI: kerjain per-panel di sesi fokus, tiap panel: (a) bangun renderer matching
screenshot, (b) wire ke feed real di mesin lu, (c) verifikasi. Urutan value: Bond Yields table →
Economic Surprise → COT gauge → Market Catalyst cards. Country grid udah jadi template pattern-nya.

## File baru turn ini
- `warroom/market_cap_target.py` — mcap target + convexity + alpha tier + decision market
- (updated) `warroom/decision_center.py` — panggil MC engine
- (updated) `warroom/compute.py` — decision_market output + mcap ke decision pkg
- (updated) `warroom/render.py` — thesis target di card + decision_market_panel + country grid

---

# LANJUTAN (turn ini) — Meters "needs data feed" DIPERBAIKI + scope statement

## Screenshot meter lu: KENAPA n/a, dan fix-nya

Verdict: meter Liquidity/Wealth/Bubble/Credit/Trend yang nampil **"needs data feed" / n/a** itu bukan
karena feed-nya kosong — **kodenya di-hardcode `value=None, status="needs data feed"`**. Ga pernah nyoba
ngitung. Padahal 4 dari 5 bisa dari harga.

Fix: `warroom/meters.py` — ngitung beneran:
- **TREND** → breadth (% di atas MA50/200) + momentum (% beat SPY63) + market structure. 100% dari harga. LIVE.
- **CREDIT** → proxy spread dari credit ETF: HY (JNK/HYG) vs IG (LQD) vs Treasury (IEF/TLT). Spread
  melebar = stress. 100% dari harga (proxy, bukan CDS beneran — di-flag di basis).
- **BUBBLE** → ekstensi harga (% di atas MA200) + realized-vol + froth breadth + (P/E dari fair_value
  kalau ada). Dari harga + valuation partial.
- **WEALTH** → momentum tema sekuler (AI=SMH, Power=XLU/VST/GEV, Nuclear=NLR/URA/CCJ, India=INDA,
  Robotics=BOTZ, Defense=ITA). 100% dari harga.
- **LIQUIDITY** → dari `funding_stress` (FRED: EFFR/reserves/RRP/TGA). **SATU-SATUNYA yang genuinely
  butuh FRED.** Tanpa FRED_API_KEY → synthetic + flag jujur.

Hasil: **10/10 meter sekarang REAL, 0 "needs data feed"** (di sandbox pakai synthetic; di cache lu, real).
Tambah ETF ke universe: LQD/JNK/AGG/BIL/TIP/EMB/SHY (credit) + BOTZ/NLR/ITA/KWEB/XLK/IGV (wealth themes).
Tiap meter punya `basis` (dari mana angkanya) + `real` flag — bisa lu audit, sesuai Golden Rule lu.

## Soal blueprint 400-engine — statement jujur (WAJIB lu baca)

Lu kirim ~40 dokumen, ~400 engine, 1500-3000 test. Gw **sengaja TIDAK** bikin 400 engine, dan ini alasannya
(sesuai prinsip lu sendiri):

1. **400 engine dalam beberapa turn = 400 fungsi kosong isinya narasi.** Itu persis "mesin narasi" yang
   VOLUME X Rule lu larang. Engine tanpa data real + validasi = dekorasi.
2. **Banyak engine butuh kelas data yang ga ada di sini**: alt-data (satelit, job postings, GitHub),
   microstructure (dealer gamma, options flow), vintage FRED, credit CDS, private-market. Semua ke-block
   di sandbox. Gw ga bisa (dan ga mau) bikin engine yang outputnya angka karangan.
3. **Prinsip lu sendiri**: "Production is earned, not default" + Golden Rule "ga ada angka tanpa basis
   data, backtest, confidence". Bikin 400 engine tanpa itu = melanggar konstitusi proyek lu.

**Yang UDAH gw bangun dengan basis data real** (bukan stub): GIP/quad regime, risk range, decision center
(entry/stop/target/invalidation), market-cap target + convexity + alpha-tier (Vol XXV Decision Quality),
decision market (efficient frontier), beta propagation, country regime grid, 10 composite meters,
walk-forward backtest (path-dependent, no-lookahead), validation suite (levels 0-9 subset).

**Yang statusnya "research/needs-data"** (jujur di-flag, bukan dipromosikan ke production): semua engine
yang butuh alt-data/microstructure/vintage. Ini SESUAI pipeline lu: Raw Discovery → Research Queue →
Validation → Production. Gw taruh di Research, bukan maksa ke Production.

**Rekomendasi gw** (sesuai alokasi lu: 10% fitur, 90% data+validasi): jangan tambah engine dulu. Prioritas:
(1) wire data real di mesin lu (build_cache + build_feeds + FRED_API_KEY), (2) jalanin run_validation --cache,
(3) engine yang lolos gate naik production, yang ga lolos tetap research. Itu Architecture Freeze + Validation
First yang lu tulis sendiri.

## File turn ini
- `warroom/meters.py` (baru) — 5 meter dari price proxy + funding
- (updated) `data.py` — 13 ETF baru (credit + wealth themes)
- (updated) `compute.py` — meters_computed di output
- (updated) `brief_export.py` — meter pakai hasil real, bukan stub
- (updated) `run_validation.py` — test meter coverage

## Dead-code candidates (gw ga hapus blind — lu review dulu)
- `warroom/discover.py` — unreferenced, kemungkinan superseded _discovery di compute
- `warroom/calibrate_lpm.py` — CLI tool, import `from lpm` broken (jalan cuma dari dalam warroom/)
- `warroom/walkforward.py` — masih di-refer run_validation (deflated_note); JANGAN hapus
Gw ga hapus karena risiko mecahin UI yang ga bisa gw test penuh di sandbox > manfaat. __pycache__ udah kebuang.

---

# LANJUTAN — DATA REAL + CAUSAL ATTRIBUTION (turn ini yang paling substansial)

## Breakthrough: gw dapet DATA REAL (akhirnya)

Masalah inti semua keluhan lu — "ticker sampah/asal bunyi" — akarnya: sandbox ga bisa Yahoo/FRED, jadi
semua run pakai sintetis. **Turn ini gw tarik data REAL dari GitHub** (domain yang diizinin):
- S&P 500 harian 505 nama, 2013-2018 (`all_stocks_5yr.csv`, 619k baris)
- Shiller: SP500+CAPE+CPI+earnings+rates, 1871-2026 (current)
- VIX harian 1990-2026 (nyampe COVID 82.7, 2022 36.5)

## Ticker validation di data REAL → 0/45 LOLOS (temuan brutal tapi jujur)

Test sinyal dashboard (formation BULLISH + RS>0 → Long) di 483 nama real, walk-forward + bootstrap:
- **0/45 kandidat teratas lolos gate.** Bootstrap p 0.39-1.0 → **ga ngalahin random.** Expectancy
  positif = beta (market naik), bukan alpha.
- Momentum factor IC: 0.019-0.024, p>0.36 → **tidak signifikan.**
- **Ini bukti "beli X karena quad" = asal bunyi.** Sinyalnya belum kebukti. Gate wajib enforce.

## Causal Attribution → jawaban pertanyaan lu (sebab tunggal vs hidden)

`warroom/causal_attribution.py` (BARU) — multi-factor regression + decomposition (Level 3-4 + Volume IX).
Dijalankan di 1820 bulan real (1872-2023):

- **"2022 = inflasi doang?" BUKAN.** CPI tidak signifikan (t=-0.82). Mekanisme = rate-change (t=-3.70) +
  valuasi. Inflasi cuma katalis.
- **"Bull run = QE doang?" BUKAN.** 60-62% return 2013-2021 = earnings growth, bukan multiple expansion.
- **"COVID = COVID doang?" IYA** (jujur). VIX 16 tenang sebelumnya, shock eksogen murni. Kadang sebab
  yang keliatan MEMANG sebabnya — disiplinnya nguji, bukan maksa cari hidden.
- **Hidden metric terkuat = prior volatility** (t=-6.53), bukan narasi makro.
- **R²=3.3%** → makro standar cuma jelasin 3.3% variance crash → crash sebagian besar TAK terprediksi.
- **2008 invisible ke makro** → butuh data kredit/leverage. Bukti perlu data tambahan, bukan ngarang.

## File turn ini
- `warroom/causal_attribution.py` (BARU) — multi-driver, decomposition, confounding detection
- `run_research.py` (BARU) — reproduce semua di data lu: `--macro`, `--tickers PANEL`, `--all`
- `research/RESEARCH_FINDINGS.md` — temuan lengkap + angka
- `research/*.parquet` + `shiller.csv` + `vix.csv` — hasil + data (panel 13MB di-drop; ada fetch helper)
- `research/fetch_sample_data.py` — regenerate panel
- (updated) `run_validation.py` — + causal-illusion test (16 PASS sekarang)

## Cara pakai di data LU
`python research/fetch_sample_data.py && python run_research.py --all` (sample), atau
`python run_research.py --tickers your_cache.parquet` (data lu, multi-regime 2008-2026 → hasil lebih kuat).

---

# LANJUTAN — Early Warning, Auto-Ingest, Master Automation, Valuation di UI

## Yang teruji & masuk turn ini
- **PANIC=BOTTOM tervalidasi** (fwd63 +6.2% vs +3.3%, p<0.001) → `early_warning.py` → tampil di
  Today's Attention saat aktif ("⚠ PANIC BOTTOM setup"). Euphoria-top di-flag lemah (jujur).
- **Auto-add ticker** → `data_ingest.py`: add_ticker/ensure/update_cache/build_panel. Ticker baru
  auto-tarik dari stooq/yfinance ke cache parquet. Sandbox: gagal graceful; mesin lu: jalan penuh.
- **Master automation** → `certify.py`: satu perintah jalanin SEMUA test, hasilkan CERTIFICATION.md
  (PRODUCTION/RESEARCH/FAIL per engine). Jawaban "gw ga mau jalanin test sendiri."
- **CAPE months di UI** → Mission Control sekarang nampilin "Valuation Context: CAPE 30.8, 95th pct,
  median 21 bulan ke -20% drawdown." Lu ga usah nerka lagi.
- **Lead-lag diuji → prediktif lemah** (jujur): beta-chain buat thematic exposure, bukan prediksi lag.

## File turn ini
- `warroom/early_warning.py`, `warroom/data_ingest.py`, `certify.py` (BARU)
- (updated) compute.py (early_warning + valuation_room di output), render.py (valuation panel + panic
  di attention), attention.py (fear-greed/panic), run_validation.py (signal-edge test)
- research/RESEARCH_FINDINGS.md §7-8, CERTIFICATION.md (auto-generated)

## UI/UX — status jujur
Turn ini gw TAMBAH ke UI: valuation context (CAPE months), panic/fear-greed di Today's Attention,
Decision Market, country grid, thesis targets. TAPI redesign penuh dari-0 (17 tab, pixel-match Nova
Capital) BELUM. Itu effort besar tersendiri. Substansi (data teruji, auto-ingest, early warning,
otomasi) udah jadi — itu fondasi yang lu tekankan berkali-kali. UI redesign penuh = langkah berikutnya.

---

# LANJUTAN — CROSS-ASSET MACRO REGIME (semua market, teruji)

Jawaban "kapan aggressive/defensive + play EV+ di setiap market" — `warroom/macro_regime.py`, diuji di
panel cross-asset real (SP500+gold+oil+dollar+rates+CPI, 1971-2023):
- **Risk-on/off regime TERUJI**: corr(score, fwd drawdown) +0.28 (p<0.0001). AGGRESSIVE (score 3, DD -2.8%)
  vs DEFENSIVE (score 0, DD -7.7%). Tampil di Today's Attention.
- **Dollar = hub**: dollar↔gold -0.22, ↔oil -0.20, ↔stocks -0.16 (semua p<0.001). Short dollar = long
  gold/oil/stocks. Connecting-the-dots cross-asset yang TERUJI (bukan lead-lag harian yang gagal).
- **Macro playbook**: stagflasi → oil kalahin stocks (+3.1% vs +0.7%); inflasi turun → risk-on.
- Ke certify.py (status PRODUCTION) + findings §9 + Mission Control.

Data baru ditarik: oil (WTI 1986), nat gas, exchange rates (dollar index proxy), gold. Panel di
research/macro_panel.parquet (72KB).

Modul turn-turn terakhir (semua data real + teruji + otomatis via certify.py):
signal_edge · causal_attribution · early_warning · data_ingest · macro_regime · backtest · certify

---

# LANJUTAN — 3 tab baru (blueprint-aligned) + TAB_SPEC + rotation

Cocokin ke blueprint lu (TAB_SPEC.md = pemetaan lengkap tab→Volume→engine→status). Tambah 3 tab yang
blueprint wajibin tapi belum ada, semua feed dari engine TERUJI:
- **Cross-Asset Macro** (VIII+III): risk-on/off timing, dollar-hub links, quad playbook, inflation play.
- **Early Warning** (#386-400): fear-greed gauge, panic-bottom, crash lead-time 12/24/36mo, valuation room.
- **Validation** (XVIII Validation Bible): signal confidence PRODUCTION/RESEARCH/REJECTED per engine +
  4-fold gate. INI yang bikin pembaca yakin — tiap sinyal ada status teruji.

Total 20 tab, correlated things dikelompokkan (ga mencar). Rotation diuji → deskriptif bukan prediktif
(§11), di-flag jujur. TAB_SPEC.md cantumin yang belum sesuai (Bonds tab, Decision Journal penuh, dll).

File: warroom/render.py (+3 render func +confidence CSS), app.py (20 tab), TAB_SPEC.md (baru),
research/RESEARCH_FINDINGS.md §11.

---

# LANJUTAN — Ticker align ke attachment + tab redesign (20→13)

- **Ticker di-align ke attachment lu**: universe nambah SUPPLY_CHAIN (nama consensus_heatmap + bottleneck
  ref: MU/AVGO/COHR/CRDO/AAOI/AXTI/LITE/GLW/APH/FORM/SITM/AEHR/ALAB/CIEN/QCOM/ARM/SMCI/TSM/dst). 207 nama,
  di-map ke thesis. Intl names (Samsung/SK Hynix/TSMC/Innolight) via data_ingest.ensure() di mesin lu.
- **Tab redesign 20→13** dikelompokkan: Macro & Regime (cross-asset+state+command), Alpha & Tickers
  (alpha+US+fairvalue), Flow & Rotation, Knowledge Graph (chains+bottleneck), Brief, Portfolio.
- JUJUR di TAB_SPEC.md: supply-chain names belum di-backtest (butuh data lu); kedalaman konten per-tab
  (Company Cards, Theme Library) belum penuh; ga bisa klaim 100% sesuai 19 attachment.

File: warroom/data.py (SUPPLY_CHAIN +universe), market_cap_target.py (thesis map), app.py (13 tab),
TAB_SPEC.md (rewrite).
