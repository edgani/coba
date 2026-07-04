# MASTER PRODUCT SPECIFICATION (MPS) — War Room Pro / Investment Intelligence OS

Deliverable yang lu bilang paling penting ("source of truth"). Ini kondensasi — bukan 1500 halaman, tapi
spec nyata yang maping Vision → Tab → Widget → Engine → Formula → Validation, plus aturan "apa yang TIDAK
BOLEH ada". Versi panjang per-volume dibangun di atas fondasi ini.

---

## VOLUME 1 — VISION & PHILOSOPHY

**Vision:** satu layar menjawab: apa yang terjadi, kenapa, efek dominonya, berapa lama, apa yang mengubah
thesis, tema/ticker mana optimal, mana beta play, masih murah atau tidak, apa risikonya, kapan berhenti
percaya. **Decision-first, zero-search, explore-not-search.**

**Prinsip inti (enforced):**
1. Production is earned, not default — hanya engine lolos `certify.py` yang jadi sinyal actionable.
2. Golden Rule — tidak ada angka tanpa test + confidence + uncertainty bound.
3. Decision quality ≠ outcome quality (Volume XXIV).
4. Setiap halaman berakhir di keputusan (So What?).

**ATURAN "TIDAK BOLEH ADA"** (dari audit doc-7, dijadikan hukum):
- ❌ formula tanpa penjelasan · ❌ skor tanpa dekomposisi · ❌ sebab-akibat tanpa confidence
- ❌ rekomendasi ticker tanpa thesis + invalidasi · ❌ data usang tanpa freshness · ❌ engine belum
  tervalidasi masuk production · ❌ watchlist tanpa alasan · ❌ rekomendasi hanya karena harga naik

---

## VOLUME 2 — UI/UX & VISUAL HIERARCHY

**Target: 70% visual, 30% teks.** Teks hanya jelasin "kenapa", bukan ngulang angka.
**UX flow (urutan berpikir):** World → Macro → Driver → Chain → Theme → Bottleneck → Ticker → Portfolio →
Research → Decision. **Asset = FILTER, bukan tab** (target; sekarang masih tab per-market — di backlog).

Visual components (target vs status):
| Visual | Untuk | Status |
|---|---|---|
| Gauge/bar meters | regime/conviction/risk | ✅ ada (Mission Control) |
| Knowledge graph interaktif | macro→company | ⚠️ ada (list+propagasi); versi node-klik-zoom = backlog |
| Bar/heat propagation | shock consequences | ✅ ada (Decision Board) |
| Bubble map (theme) | capital flow × momentum | ❌ backlog |
| Sankey (sebab-akibat) | flow | ❌ backlog |
| Treemap/radar/waterfall | allocation/quality/attribution | ❌ backlog |

---

## VOLUME 3 — TAB SPECIFICATION (13 tab, lihat TAB_SPEC.md)

Mission Control · Macro & Regime (+Thesis/Playbook) · Early Warning · Alpha & Tickers (+Decision Board +
Investment Memos) · Crypto · Commodities · FX · IHSG · Flow & Rotation · Knowledge Graph · Validation ·
Brief · Portfolio (+Decision Journal). Target reorder: Mission Control → War Room → Macro → Regime →
Knowledge Graph → Theme → Decision → Ticker → Portfolio → Validation → Research (backlog).

---

## VOLUME 4 — WIDGET SPECIFICATION (key widgets, acceptance criteria)

| Widget | Engine | Acceptance |
|---|---|---|
| Today's Attention (6 items) | attention.py | ranks by magnitude; empty→"quiet day" |
| Signal Confidence | render._confidence_panel | every signal labelled PRODUCTION/RESEARCH/REJECTED |
| Risk Regime | macro_regime.risk_regime | score 0-3 + tested drawdown expectation |
| Fear-Greed + Panic | early_warning | panic setup only when VIX>80pct + oversold |
| Crash Risk (12/24/36mo) | crash_lead | probability not binary; honest bounds |
| Valuation Room | signal_edge.valuation_room | CAPE pct + months-to-drawdown |
| Decision Board | decision_engine | theme→best equity→beta→invalidation |
| Investment Memo | investment_memo | role/chain/exp-mcap/invalidation/decision-score |
| Thesis & Playbook | thesis_playbook | hypothesis/mechanism/why-now/devil's-advocate |
| Knowledge Graph | knowledge_graph | propagation w/ decaying confidence + tickers |

---

## VOLUME 5 — FORMULA (explainability WAJIB — every score decomposed)

- **Risk Regime** = trend(>10mo MA) + momentum(6mo>0) + dollar-falling. Tested: corr(score, fwd DD) +0.28, p<0.0001.
- **Fear-Greed** = 40%·(1−VIX_pct) + 30%·(1−breadth_below_50ma) + 30%·momentum_z. Tested: corr(greed, fwd) −0.21.
- **Crash prob** = base_rate[H] × composite_multiplier{score2=1.35}. Tested: 15%→27% @ 24mo.
- **Convexity EV** = Σ P(scenario)·return(scenario); tail_ratio = upside/downside.
- **Decision (best-risk-reward)** = 50 + EV·0.4 + tail·5, clamp 0-100.
- **RS top-decile** = cross-sectional rank(6mo relative-to-EW) > 0.90. Tested: lift 2.08x.

Semua formula punya dekomposisi (aturan: no magic number). Bobot Liquidity/dll finalized saat data lengkap.

---

## VOLUME 6 — KNOWLEDGE GRAPH (knowledge_graph.py)

60 typed edges, network. Tiap edge: sign, lead_days, confidence, strength, half_life, regime, evidence,
**tested**. Chains: War→Oil→Tanker→...→Consumer · AI→HBM→DRAM→TSV→CoWoS→Substrate→ABF · Power→Transformer→
Copper→Utility→Nuclear→Uranium · Tariff→Manufacturing→Freight · Fed/PBOC/BOJ transmission · Defense→Drone→
RareEarth. Propagasi 2nd/3rd/4th order, confidence meluruh tiap hop. Node→ticker (NODE_TICKERS).
**Edge tested=True hanya cross-asset (dollar-hub, p<0.001); sisanya structural knowledge (ditandai).**

---

## VOLUME 7 — TICKER INTELLIGENCE (investment_memo.py)

Ticker = **Investment Memo** (bukan watchlist): Company · Role · Chain node · Supply/Demand drivers ·
**Expected Market Cap (bull/base/bear)** · Convexity/EV · Alpha tier · Catalysts · Beta play · Alternative
· **Invalidation** · **Decision (best-risk-reward score, bukan BUY)**. Fundamental per-company (revenue/
EBIT/ROIC/margin/capacity/customer/competitor) = butuh data feed → mesin lu.

---

## VOLUME 8 — MACRO INTELLIGENCE (macro_regime.py + causal_attribution.py)

Setiap data macro → mekanisme + winners/losers + duration + analog + invalidation (bukan tabel angka).
Cross-asset playbook tested (§9). Multi-driver attribution: crash = multi-faktor, R²~3% → largely
unpredictable (§2). Surprise/expectation/analog engine = backlog (butuh consensus + historical data).

---

## VOLUME 9 — DECISION ENGINE (decision_engine.py + thesis_playbook.py)

Theme/shock → best equity → why (graph mechanism) → beta chain (2nd/3rd order) → invalidation →
alternative. Thesis card (hypothesis/evidence/mechanism/probability/KPI/invalidation). Playbook per regime
(phase-by-phase, tested flagged). Why-now/why-not/wait + devil's advocate.

---

## VOLUME 10 — VALIDATION (certify.py — 9 engines)

4-fold gate: mechanism + statistical + value-add + out-of-sample. Status: backtest ✅, panic-bottom ✅,
cross-asset ✅, crash-lead ✅, valuation ✅, KG+decision 🔬, RS-edge 🔬, euphoria 🔬, naive-signal ✕.
Walk-forward + bootstrap + IC + event study. Reproduce: `python certify.py`.

---

## VOLUME 11-15 — RESEARCH / TESTING / BACKEND / DATA / AI (status)

- **Research OS**: hypothesis→research→validation→production→monitoring→retirement. Decision Journal
  (#399) ✅. Research Queue / Research ROI / knowledge versioning = backlog.
- **Testing**: run_validation.py + certify.py + run_research.py. Acceptance tests = partial.
- **Backend/Data**: parquet cache + data_ingest (auto-add ticker). Data lineage/freshness/quality score,
  master data dictionary, entity dictionary = SPEC'd here, implementation = backlog.
- **AI Agent**: reasoning SOP (Volume IX) embedded as behavior; standalone orchestration = backlog.

---

## BACKLOG (Tier 2/3 — masuk hanya lewat hypothesis→validation, per aturan lu)

Temporal/Saturation/Consensus/Expectation/Narrative/Capital-Cycle/Reflexivity/Second-Derivative/
Edge-Crowding/Market-Memory/Analog/Options-positioning/Data-lineage/Contradiction/Sensitivity/
Counterfactual/Bubble-map/Sankey/interactive-node-graph/asset-as-filter. ~100 engine di audit lu.
**Value Audit gate:** (1) incremental decision value? (2) data cukup berkualitas? (3) manfaat > kompleksitas?
Kalau tidak → didokumentasikan sebagai ide, TIDAK masuk production.

---

## STATUS JUJUR (framing lu)
- Arsitektur: ✅ ~99% · Engine inti: ✅ ~90% · Validation framework: ✅ ~90%
- Decision experience (memo/thesis/playbook/decision-board): 🔨 ~70% (dibangun; butuh data buat penuh)
- Visual (interactive graph/bubble/sankey): 🔨 ~40% (backlog)
- Implementasi teknis (DB/API/scheduler/vector-db): 🔨 ~50% (spec ada, engineering backlog)
- **Bottleneck sekarang = data + validasi + visual, BUKAN nambah engine.** Sebagian besar butuh data yang
  hanya ada di mesin lu atau berbayar. Yang bisa dibangun + diuji dengan data yang gw akses — sudah ada.
