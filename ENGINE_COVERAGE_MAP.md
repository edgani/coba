# ENGINE COVERAGE MAP — jawaban jujur "udah semua 400 engine?"

**Jawaban singkat: BELUM, dan ga akan jujur kalau gw bilang udah.** Tapi lu bener — **400 engine itu ga
harus dipisah semua.** Banyak yang overlap, mergeable, atau sebenarnya framework/SOP (bukan kode). Ini
maping jujurnya: mana yang UDAH ada (dengan data real), mana yang MERGED ke engine existing, mana yang
GENUINELY MISSING (butuh data yang ga ada di sandbox).

Prinsip yang gw pegang (dari VOLUME X + Golden Rule lu): **engine tanpa data real + validasi = dekorasi.**
Gw ga bikin 400 fungsi kosong. Gw bikin yang bisa di-back dengan data + gw flag sisanya jujur di pipeline
Research (bukan Production) — persis Raw Discovery → Research Queue → Validation → Production yang lu tulis.

---

## ✅ SUDAH ADA (data real, ke-wire, ke-render)

| Blueprint | Modul | Status |
|---|---|---|
| Macro/GIP quad regime | `engines/gip_engine.py` | quad sign-mapping teruji (Q1-4) |
| Risk Range (Hedgeye) | `gcfis/engines/risk_range_hedgeye.py` | TRADE/TREND/TAIL band |
| Crash Meter (#Macro/Crash) | `_crash` + `gcfis/crash_bottom` | internals+shock, LIVE |
| **10 Composite Meters** | `warroom/meters.py` (BARU) | Trend/Credit/Bubble/Wealth dari price proxy, Liquidity dari FRED — **10/10 LIVE, 0 "needs feed"** |
| Decision Engine (entry/stop/target/invalidation) | `warroom/decision_center.py` | 5 stop, T1-T3, **stop di luar entry zone (bug fixed di source)** |
| Market-Cap Target + Convexity (Vol XXV Decision Quality) | `warroom/market_cap_target.py` | bull/base/bear mcap → price, EV, alpha-tier, kill-thesis |
| Decision Market (efficient frontier) | `market_cap_target.decision_market` | max-EV/min-risk/max-convexity per thesis |
| Beta Propagation (#387-390 chain) | `warroom/thesis_beta.py` + `beta_play.py` | beta/convexity per tier |
| Country Regime Grid (Doc 3 Market DNA partial) | `warroom/country_regime.py` (BARU) | 16 negara, price-proxy quad |
| **Today's Attention (#396 Human Attention)** | `warroom/attention.py` (BARU) | 6 hal top hari ini, ranked by magnitude |
| Walk-Forward Backtest (Level 5 + gatekeeper) | `warroom/backtest.py` (BARU) | path-dependent, no-lookahead, bootstrap — **ganti gatekeeper random** |
| Validation Suite (Level 0-9 subset) | `run_validation.py` | 16 test executable + 18 gated jujur |
| Causal Chains (Chain Engine) | `warroom/causal_chain.py` | chain integrity |
| Cross-Asset Coherence | `_xasset` | validated |
| Portfolio Risk | `warroom/risk.py` | conviction book |
| Fair Value (Valuation base/bull/bear) | `warroom/fair_value.py` | analyst + fwd-multiple |

## 🔷 MERGED (banyak engine numbered = satu modul; ga perlu dipisah, lu bener)

Blueprint lu punya ratusan engine yang sebenarnya **satu konsep dipecah kecil-kecil**. Gw gabung:

- **#Meters group** (Liquidity/Bubble/Credit/Trend/Wealth/Rotation/Macro/Crash/Entry/Conviction) →
  1 modul `meters.py` + brief_export. Itu ~10 "engine" jadi 1 file.
- **Convexity Engine + Leverage + Thesis Elasticity + Second Derivative + Capital Multiplier + Alpha
  Cascade + Risk-Adjusted Beta + Asymmetric Return** (8 "engine" di doc lu) → semua overlap jadi
  `market_cap_target.py` (convexity/EV/tail/alpha-tier) + `thesis_beta.py` (beta chain). Itu bukan 8
  engine terpisah — itu 8 sudut pandang dari SATU perhitungan asimetri.
- **Why Now / Why Hasn't Market Seen / What Market Missing / Exit Liquidity / Thesis Saturation /
  Narrative / Attention** → ini semua **pertanyaan reasoning**, bukan engine. Masuk ke reasoning SOP
  (LEVEL 1-10 VOLUME IX), bukan kode terpisah.
- **Expected Market Cap → Portfolio Weight → Capital Allocation** → 1 flow di `market_cap_target`
  (`suggested_weight`).

## 🔬 RESEARCH QUEUE (butuh data yang GA ADA di sini — di-flag, bukan dikarang)

Ini bukan "ga dikerjain" — ini **sengaja di Research, bukan Production**, karena datanya ke-block:

| Engine | Butuh data | Kenapa belum |
|---|---|---|
| Self-Discovery / New-Chain Detector (#386-390) | Berita/paten/embedding korpus + LLM loop mingguan | Butuh pipeline scheduled + alt-data; correlation sementara ≠ chain (lu sendiri bilang jangan ngarang hubungan) |
| Latent Theme Discovery (#391) | Clustering cross-asset + news | Sama — butuh corpus |
| Auto-Hypothesis + Research Economics (#394-395, Vol XXIII) | Backtest infra + EV estimator | Butuh data real dulu buat EV yang bener |
| Meta-Learning / Self-Reweighting (#393, #400) | 3 thn track record | Akrual seiring waktu (tracker) — ga bisa di-backtest instan |
| Alpha Accounting (Module 9) | Live portfolio returns | Butuh live trading log |
| Dataset Value/ROI (Module 6-7) | Katalog dataset + IC per dataset | Butuh data eksternal berbayar |
| Liquidity full (Fed/ECB/BOJ/M2 global) | FRED + ECB + BOJ API | FRED ke-block di sandbox; LIVE di mesin lu |
| Vintage/Revision tests (Cat 4, Level 0) | ALFRED vintage FRED | Ga ada di sandbox |
| Survivorship-free universe (Cat 3) | Delisted-inclusive history | Universe sekarang = survivor |
| Causality suite (Granger/TE/PCMCI, Cat 7, Level 4) | Multi-dekade clean data | Butuh cache real |
| Company Knowledge Cards (Part 9) | Fundamental per-nama (revenue/moat/roadmap) | Butuh fundamental feed |
| Market/Thesis Autopsy (Part 6-7) | Research manual (dokumen, bukan kode) | Ini tulisan, bukan engine |

## ❌ FRAMEWORK/SOP (bukan kode — Volume IX-XXV)

Reasoning framework (LEVEL 1-10), Research Philosophy (Rule 1-14), Validation Bible, Research Manual,
Governance — ini **dokumen/SOP**, bukan engine yang di-code. Sebagian udah ke-embed sebagai PERILAKU di
engine (calibrated-or-silent P(win) = Rule 8 "unknown better than wrong"; convexity+EV = Rule 2 "maximize
EV not accuracy"; kill-thesis = Rule 4 "every thesis needs anti-thesis"; decision≠outcome = Vol XXIV).

---

## Kesimpulan jujur

- **~15 engine core UDAH jalan dengan data real.** Bukan 400. Tapi 400 lu itu realistis ~40-50 engine
  unik + ratusan varian/sudut-pandang + puluhan dokumen SOP.
- **Design SEKARANG berubah**: entry=stop bug fixed di semua tab, Today's Attention panel baru di atas
  Mission Control, tiap rec card nampilin thesis target + convexity + alpha tier + kill-thesis.
- **Yang belum**: semua yang butuh alt-data/microstructure/vintage/fundamental/live-log. Itu **ga bisa
  gw karang** — dan lu sendiri yang bikin aturan itu (Golden Rule + Production is earned).
- **Path bener** (alokasi lu: 10% fitur, 90% data+validasi): wire data real di mesin lu → run_validation
  --cache → engine yang lolos 4-gate naik Production, sisanya tetap Research. Itu Architecture Freeze +
  Validation First.

Gw ga bakal bilang "udah semua" kalau belum. Itu justru ngelanggar hal paling inti yang lu minta.
