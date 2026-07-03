# TAB SPECIFICATION — 13 tab (redesign, dikelompokkan) vs blueprint lu

Verdict: 20 tab mencar → **13 tab dikelompokkan logis** (yang berkorelasi digabung, per permintaan lu).
Plus ticker universe di-align ke nama attachment lu (consensus_heatmap + supply chain).

## 13 tab → blueprint → isi

| # | Tab | Gabungan dari | Blueprint | Isi |
|---|---|---|---|---|
| 1 | **Mission Control** | (hub) | #396 + IV | Today's Attention (6 hal), meters, rec cards, valuation context |
| 2 | **Macro & Regime** | Cross-Asset Macro + Market State + Command Center | VIII + III + X | Risk-on/off timing, dollar-hub, quad playbook, regime state, decision engine |
| 3 | **Early Warning** | (baru) | #386-400 + forecast | Fear-greed, panic-bottom, crash lead-time 12/24/36mo, valuation room |
| 4 | **Alpha & Tickers** | Alpha Center + US Stocks + Fair Value | XII + XVII | Conviction ranking, Decision Market, US setups, fair value — DI SINI ticker keluar |
| 5 | **Crypto** | Crypto | IV (Crypto DNA) | Crypto setups + risk-curve |
| 6 | **Commodities** | Commodities | IV (Commodity DNA) | Commodity setups + COT |
| 7 | **FX** | FX | IV (FX DNA) | FX setups |
| 8 | **IHSG** | IHSG | IV (IHSG DNA) | IDX + bandarmologi |
| 9 | **Flow & Rotation** | Cross-Asset Rotation + Flow | (flow) | RRG rotation map + ETF/sector flow |
| 10 | **Knowledge Graph** | Chains + Bottleneck + Company Cards + Catalysts | IX + VI + Part 8-9 | Causal chains, **Company Knowledge Cards (68 names, role+catalysts+convexity)**, Catalyst Timeline, bottleneck |
| 11 | **Validation** | (baru) | XVIII Validation Bible | Signal confidence PRODUCTION/RESEARCH/REJECTED + 4-fold gate |
| 12 | **Brief** | Morning Brief + Briefing | XV + II | Daily brief + reasoning narrative |
| 13 | **Portfolio** | Track Record + **Decision Journal** + Risk & Health | XIX + #399 + Risk | Performance, trades, **Decision Journal (decision quality vs outcome)**, portfolio risk, health |

## TICKER — sekarang di-align ke attachment lu
Universe nambah `SUPPLY_CHAIN` (data.py) = nama consensus_heatmap + bottleneck reference lu:
MU, AVGO, MRVL, AAOI, COHR, CRDO, AXTI, LITE, GLW, APH, FORM, SITM, AEHR, HIMX, ALAB, FN, AMKR, ANET,
CIEN, QCOM, ARM, ASML, SMCI, DELL, TSM, ETN, VRT, GEV, POWL, MP, LNG, dst (207 nama total). Di-map ke
thesis (photonics/ai_compute/ai_power) → dapat convexity target.

**Nama internasional** (Samsung 005930.KS, SK Hynix 000660.KS, TSMC 2317.TW, Innolight 300308.SZ,
Eoptolink 300502.SZ, Browave 3163.TWO, FOCI 3363.TWO) → butuh yfinance di mesin lu. Tambah via:
`from warroom import data_ingest as DI; DI.ensure(["005930.KS","000660.KS","300308.SZ",...])` → auto masuk cache.

## JUJUR — yang BELUM sesuai/teruji
- **Ticker supply-chain BELUM di-backtest** — di sandbox ga ada data harganya. Metodologi (RS top-decile,
  event study) udah teruji di S&P; nama spesifik lu butuh data lu buat divalidasi (`run_research.py --tickers`).
- **Konten dalam per-tab belum sedalam blueprint**: Company Knowledge Cards (Part 9), Theme Library
  (Part 8), Market Autopsy (Part 7) — belum dibangun penuh. Struktur & engine ada; konten kurасi belum.
- **Bonds** belum jadi tab tersendiri (rates ada di Macro & Regime).
- **Options/Greeks/COT empiris** — data ke-block/proprietary.
- Gw BELUM bisa klaim "tiap tab 100% sesuai 19 attachment" — struktur & engine align, kedalaman konten belum penuh.
