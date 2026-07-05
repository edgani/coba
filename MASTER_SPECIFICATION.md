# MASTER SPECIFICATION — GCFIS v1.0 (Global Capital Flow Intelligence System)

**Status: SCOPE FROZEN.** Ini source-of-truth: catalog SEMUA engine dari V40 (63k LOC library) + lean core
(teruji) + backlog audit, disortir ke 3-layer architecture dengan status validasi + kebutuhan data.
Tujuannya: **ga ada yang ilang, ga ada yang ambigu, implementasi jalan dari sini.**

Aturan promosi: engine cuma naik ke **Layer 1 (Production)** kalau lolos 4-fold gate (mechanism +
statistical + decision-value + out-of-sample). Kalau belum → **Layer 2** (exists, needs validation) atau
**Layer 3** (idea, not built). Ini yang bikin sistem dipercaya 10-20 tahun, bukan kumpulan fitur.

---

## LAYER 1 — CORE OS (TERUJI, dipakai buat keputusan harian)

Engine yang udah lolos validasi di data real (bukti: `certify.py` + RESEARCH_FINDINGS.md).

| Engine | Fungsi | Status | Bukti | Lokasi |
|---|---|---|---|---|
| Cross-Asset Macro | dollar hub → gold/oil/stocks | ✅ PRODUCTION | corr −0.22, p<0.001 | lean/engines.py, v40/cross_asset.py |
| Risk Regime | aggressive/defensive timing | ✅ PRODUCTION | corr(fwd DD) +0.25, p<0.001 | lean/engines.py |
| Panic-Bottom | fear→buy contrarian | ✅ PRODUCTION | fwd63 +6% vs +3%, p<0.001 | lean/engines.py, v40/crash_bottom.py |
| Valuation Room | CAPE→forward + months-to-DD | ✅ PRODUCTION | CAPE deciles tested | lean/engines.py |
| Crash Lead-Time | P(crash 12/24/36mo) probabilistik | ✅ PRODUCTION | 15%→27% @24mo, p=0.0001 | lean/engines.py |
| RS Top-Decile | ticker screen (cross-sectional) | ◐ RESEARCH | lift 2.14x, alpha not sig | lean/backtest.py, v40/surge.py |
| Knowledge Graph | shock propagation + typed edges | ◐ RESEARCH | 3 edges tested, rest structural | lean/graph.py |
| Decision Engine | theme→best equity→beta→invalidation | ◐ RESEARCH | structure works, edges need data | lean/graph.py |
| Investment Memo | per-ticker: role/mcap/decision | ◐ RESEARCH | assembled from tested parts | lean/graph.py |

---

## LAYER 2 — INSTITUTIONAL EXTENSIONS (ADA di V40, butuh validasi sebelum Production)

Engine yang udah dibangun di V40 (kode jalan) tapi BELUM lolos validasi out-of-sample. Advisor lu (doc 22)
bilang "jangan dibuang". Masuk Production hanya setelah divalidasi di data lu.

| Engine | Fungsi | V40 file | Kebutuhan validasi |
|---|---|---|---|
| **Liquidity** ⭐ | QE/QT/RRP/TGA/reserves/dollar-liquidity → risk assets | engines/liquidity.py | corr liquidity-impulse vs fwd return, cross-regime |
| **Positioning** ⭐ | dealer/CTA/gamma/vol-control exposure | engines/positioning.py, dealer.py | needs options data (paid); backtest gamma-flip |
| **Flow** ⭐ | ETF/foreign/institution/retail flow, rotation | engines/flow.py, flow_type.py, flow_regime.py | flow→return predictive test |
| **Fragility** ⭐ | market/liquidity/leverage/funding fragility, crowding | engines/fragility.py | fragility→drawdown event study |
| **Change Detection** ⭐ | hidden regime shift, correlation/structure break | engines/change_detection.py, core/change_core.py | break→forward vol/return test |
| **Reflexivity** | price↑→flows↑→price↑ feedback loops | engines/reflexivity.py | reflexive-momentum vs mean-reversion regime test |
| **Accumulation** | institutional accumulation/distribution, dark pool | engines/accumulation.py, broker_flow.py | accumulation→forward return test |
| **Internals/Breadth** | advance-decline, participation, leadership | engines/internals.py | breadth-thrust→forward return (known edge, revalidate) |
| **Rotation** | country/sector/factor/theme rotation | engines/rotation.py | rotation-momentum predictive test (prior: weak) |
| **Response Zone** | macro support/resistance/liquidity/demand zones | engines/response_zone.py | zone-reaction hit-rate test |
| **Narrative** | AI/power/defense narrative momentum + fatigue | engines/narrative.py | narrative→sector return lead test |
| **Market Mode** | risk-on/off/melt-up/crisis/bubble/transition | engines/market_mode.py | mode→forward return/vol test |
| **Shock** | oil+40%/dollar+15%/war/credit-event simulation | engines/shock.py | historical shock-response calibration |
| **Lead-Lag Discovery** | auto-find leading indicators (copper→AI, etc) | engines/leadlag_discovery.py | **TESTED: daily lead-lag NOT predictive (p>0.5)** → keep as exploration only |
| **Regime HMM** | hidden-markov regime states | engines/regime_hmm.py | regime-persistence + forward-return test |
| **Forward Macro** | 6-24mo macro projection | engines/forward_macro.py | forecast accuracy backtest |
| **Bottleneck Engine** | supply-chain chokepoint scoring | engines/bottleneck_engine.py | bottleneck→pricing-power/return test |
| **Elimination** | disqualification filter (why OUT) | engines/elimination.py | rule validity per asset class |
| **Meta/Decision Stack** | combine engines → final desk verdict | meta/decision_stack.py, final_desk.py, regime_meta.py | ensemble out-of-sample vs single-engine |
| **Rich Ticker Card** | 40+ field per-ticker dossier display | components/rich_ticker_card.py (1974 LOC) | display layer — data-dependent, not a signal |
| **Market Panels / Causal Map / Options Layer** | rich visual components | components/*.py | display layer |

---

## LAYER 3 — RESEARCH LAB (IDE dari audit lu, BELUM dibangun — masuk lewat hypothesis→validation)

Dari dokumen 17-25. Ini backlog, BUKAN wajib. Value-Audit gate: (1) incremental decision value? (2) data
cukup? (3) manfaat > kompleksitas? Kalau enggak → tetap dokumentasi, ga masuk Production.

**Alpha discovery:** Multibagger Engine (10x-100x screen: TAM×moat×op-leverage×supply-constraint×
institution-entry), Beta-Play multi-level (done in lean), Expected-Market-Cap deep (revenue/margin/FCF/
multiple decomposition — needs fundamentals), Optionality, Future-TAM, Mispricing ("why market wrong").

**Company deep research:** Ticker Dossier 100-card, Moat Engine (network/switching/patent/scale scoring),
Management Quality, Capital Allocation, Ownership (13F/insider/ETF/dark-pool), Earnings Quality, Valuation
multi-model (DCF/reverse-DCF/EV-EBITDA/SoP), Competitor Landscape. **All need paid fundamental data.**

**Multi-market:** Global Markets (US/EU/China/Japan/India/IDX/Korea/Taiwan/LatAm/ASEAN), Country Rotation,
per-asset Playbook (each market different screener/scoring), Market DNA (what actually drives each market),
Commodity Engine (supply/demand/inventory/curve per commodity), FX Engine, Bond Engine, Credit Engine.

**Decision theory:** Expected Value / Kelly / Asymmetry / Opportunity-Cost ("why A not B") / Convexity /
Margin-of-Safety, Position Sizing, Portfolio Construction (alpha/correlation/convexity, not mean-variance).

**Market expectation:** Surprise Engine (actual vs expected), Expectation Revision, Consensus, Saturation,
Attention (what market focuses on), Contrarian, Dispersion.

**Time & memory:** Time-Horizon (1wk-10yr), Signal/Info Half-Life, Market Memory (inventory→price lag),
Analog Search (today ≈ 1995/2003/2016), Future-Path (soft-landing 38%/reflation 26%/... → click changes
whole dashboard), Historical Replay (pick past date, see what dashboard knew, no look-ahead).

**Meta/self-improvement:** Forecast Tracker, Engine Competition, Weight Adaptation (only on OOS proof),
Meta-Learning, Model Drift, Feature Importance, Ablation, Self-Critique, Devil's Advocate agent.

**Data platform (doc 25 — the real gap):** Data Lineage, Feature Store (compute-once), Entity Master
(NVDA→ticker/CUSIP/supplier/customer/ETF/competitor), Time Engine (release/effective/revision date →
no look-ahead), Data Revision Engine, Data Quality Score (auto-downweight bad data), Version Control,
Config Engine (no hardcoded thresholds), Experiment Registry, Production Gating, Decision Replay,
Reproducibility, Engine Dependency Map.

**Knowledge/case libraries:** Case-Study Library (NVDA/AMZN/TSLA/SNDK 100x — why), Failure Library
(Enron/FTX/SVB/Nikola — why), False-Signal Library (yield-curve false alarms), Indicator Scorecard,
Playbook Database, Knowledge-Coverage Engine (what we DON'T know yet).

---

## VALIDATION FRAMEWORK (doc 20 — the lab, not a checklist)

Setiap engine, sebelum Production, lewat: dataset + period + N-obs disclosed · IC + rank-IC · precision/
recall (if classifier) · walk-forward · bootstrap · permutation/placebo · sensitivity · ablation ·
survivorship-bias check · look-ahead check · data-revision check · cross-market · cross-decade ·
economic + statistical significance · stability score. Fail one → status Research, not Production.
Automation: `certify.py` runs this and emits status per engine.

---

## IMPLEMENTATION ORDER (doc 26 — freeze then build, don't improvise)

1. **Freeze this spec** (done — this document).
2. **Layer 1 = the running product** (lean core, already tested & deployed).
3. **Promote Layer 2 one-by-one**: take each V40 engine → validate on your data → if pass, wire into
   dashboard as Production; if fail, keep in Research tab with honest label.
4. **Layer 3 only via hypothesis→validation**, never bulk. Value-Audit gate each.
5. **Data platform (Layer 3 data)** is the true long-term unlock — without Feature Store / Entity Master /
   Time Engine, 200 engines will drift and conflict. Build this BEFORE scaling engine count.

## HONEST BOTTLENECK (why this matters more than engine #201)
Per your own advisors (docs 24-26): scope is 95-99% done. The project will NOT fail from a missing engine.
It fails from: bad data, weak validation, non-robust formulas, overfitting, unmaintained knowledge graph,
too many features with no incremental value. So the work now is **validation + data quality + specification
discipline**, not more brainstorming. Most Layer-2/3 engines need data that is either paid (fundamentals,
options, 13F, dark-pool) or only on your machine — that is the real constraint, honestly stated.
