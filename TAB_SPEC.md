# TAB SPECIFICATION — pemetaan blueprint lu → tab dashboard

Verdict: gw cocokin struktur tab ke blueprint lu (19 attachment + Volume I-XXV + 400 engine). Ini
pemetaan jujurnya — tab mana, isinya apa, feed dari engine mana, status teruji/belum. **20 tab sekarang**
(3 baru gw tambah biar sesuai emphasis blueprint: Cross-Asset Macro, Early Warning, Validation).

## Tab sekarang → blueprint

| # | Tab | Blueprint (Volume/#) | Isi | Engine | Status |
|---|---|---|---|---|---|
| 1 | **Mission Control** | #396 Human Attention + IV War Room | Today's Attention (6 hal), meters, rec cards, valuation context, confidence | attention, meters, decision_center | ✅ wired |
| 2 | **Cross-Asset Macro** ⭐baru | VIII Macro + III Market DNA | Risk-on/off timing, dollar-hub links, quad playbook, inflation play | macro_regime | ✅ TESTED |
| 3 | **Early Warning** ⭐baru | #386-400 self-evolution + forecast | Fear-greed gauge, panic-bottom, crash lead-time (12/24/36mo), valuation room | early_warning, crash_lead, signal_edge | ✅ TESTED |
| 4 | **Validation** ⭐baru | XVIII Validation Bible | Signal confidence (PRODUCTION/RESEARCH/REJECTED per engine), 4-fold gate | certify.py | ✅ TESTED |
| 5 | Morning Brief | XV Research SOP | Daily brief | brief_export | wired |
| 6 | Briefing | II Reasoning | Reasoning narrative | briefing | wired |
| 7 | Command Center | X Scoring | Regime + decision engine | compute | wired |
| 8 | Alpha Center | XII Ticker Discovery + XVII Scoring | Conviction ranking + Decision Market (efficient frontier) | decision_market, market_cap_target | wired |
| 9 | Cross-Asset Rotation | (rotation) | RRG rotation map | rotation | wired (deskriptif) |
| 10 | Causal Chains | IX Chain & Bottleneck / VI Knowledge Graph | Causal chains, beta propagation | causal_chain, thesis_beta | wired |
| 11 | US Stocks | IV Market Engine (US DNA) | US setups + fair value | compute, fair_value | wired |
| 12 | Crypto | IV Market Engine (Crypto DNA) | Crypto setups + risk-curve | compute, rotation | wired |
| 13 | Commodities | IV Market Engine (Commodity DNA) | Commodity setups + COT | compute | wired |
| 14 | FX | IV Market Engine (FX DNA) | FX setups | compute | wired |
| 15 | IHSG | IV Market Engine (IHSG DNA) | IDX setups + bandarmologi | compute | wired |
| 16 | Flow | (flow) | ETF/sector flow | compute | wired |
| 17 | Bottleneck | IX Bottleneck | Supply-chain bottleneck + node template | bottleneck | wired |
| 18 | Market State | VIII Macro regime | Regime state detail | compute | wired |
| 19 | Track Record | XIX QA/Monitoring + Decision Journal #399 | Performance, open/closed trades | tracker | wired |
| 20 | Risk & Health | XV Risk Engine | Portfolio risk, system health | risk | wired |

## Yang SUDAH sesuai blueprint
- Market DNA per market (US/Crypto/Commodity/FX/IHSG) → 5 tab market ✓
- Macro engine + cross-asset → Cross-Asset Macro + Market State ✓
- Chain & Bottleneck + Knowledge Graph → Causal Chains + Bottleneck ✓
- Scoring + Ticker Discovery → Alpha Center ✓
- Forecast + Early Warning (#386-400) → Early Warning tab ✓
- Validation Bible (XVIII) → Validation tab ✓ (INI yang bikin pembaca yakin — tiap sinyal ada statusnya)
- Human Attention (#396) → Mission Control Today's Attention ✓
- Decision Quality (XXIV-XXV) → convexity/EV di Alpha + market_cap_target ✓

## Yang BELUM (jujur — butuh data/effort tambahan)
- **Bonds** sebagai market tab tersendiri (blueprint Market DNA sebut Bonds) — sekarang rates ada di macro,
  belum ada tab bonds khusus (butuh data yield curve lengkap: 2Y/10Y/credit).
- **Decision Journal** (#399) penuh — sekarang Track Record nyimpen trades; jurnal keputusan +
  review-6-bulan belum otomatis.
- **Research Queue / Alpha Accounting** (Volume XXIII) — research-ops, belum jadi tab.
- **Self-Discovery / New-Chain Detector** (#386-390) — butuh corpus + LLM loop terjadwal, belum.
- **Options/Greeks/COT empiris** — data proprietary/ke-block (lihat RESEARCH_FINDINGS.md).

## Prinsip yang di-enforce (sesuai permintaan lu)
1. Yang berkorelasi/link DIKELOMPOKKAN, ga mencar: cross-asset macro dalam 1 tab, early warning dalam
   1 tab, validasi dalam 1 tab.
2. Cuma yang lolos `certify.py` yang ditampilkan sebagai sinyal actionable; sisanya di-label RESEARCH.
3. Tiap angka bisa ditelusuri ke test (Validation tab + RESEARCH_FINDINGS.md).
