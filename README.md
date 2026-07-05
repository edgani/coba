# War Room Pro — Investment Research OS (lean rebuild)

Dibangun ulang dari 0: **6 file kode** (bukan 49), cuma engine yang **TERUJI**, jalan cepat, tiap angka
traceable ke test. Ganti versi lama yang bloated.

## Struktur (FLAT — deploy-ready untuk Streamlit Cloud, app.py di root repo)
```
app.py        # dashboard 8 tab (Streamlit) — MAIN FILE
data.py       # universe + loading (cache real → yfinance → sintetis fallback)
backtest.py   # walk-forward + bootstrap + RS top-decile signal + surge-lift
engines.py    # SEMUA engine teruji: risk regime, cross-asset, fear-greed/panic, crash-lead, valuation, ranking
graph.py      # knowledge graph + propagasi + decision engine + investment memo + thesis + playbook
certify.py    # master validation → CERTIFICATION.md
research/     # data real (S&P panel, Shiller, VIX, macro panel) + RESEARCH_FINDINGS.md
data/         # bottleneck_reference.json (nama supply-chain kurasi)
requirements.txt
```

## Deploy ke Streamlit Cloud
1. Push semua file ini ke root repo GitHub lu (app.py di root, BUKAN dalam subfolder).
2. Streamlit Cloud → New app → main file = `app.py`.
3. Selesai. (Struktur flat = import antar-file langsung, ga ada masalah package path.)

## Jalanin
```bash
pip install -r requirements.txt
streamlit run app.py          # dashboard
python certify.py             # validasi semua engine → CERTIFICATION.md
```
Di mesin lu, data real (cache/yfinance) otomatis kepake — semua angka jadi real. Tambah ticker:
`from wr import data; data.add_ticker("005930.KS")` (Samsung), dst.

## Yang TERUJI (di data real, lolos certify)
| Engine | Status | Bukti |
|---|---|---|
| Cross-asset macro (dollar hub) | PRODUCTION | corr −0.22, p<0.001 |
| Risk regime (aggressive/defensive) | PRODUCTION | corr(fwd DD) +0.25, p<0.001 |
| Panic-bottom (fear→buy) | PRODUCTION | fwd63 +6% vs +3%, p<0.001 |
| Valuation room (CAPE→forward) | PRODUCTION | CAPE deciles tested |
| Ticker RS top-decile | RESEARCH | lift 2.14x (alpha belum signifikan) |
| Knowledge-graph edges | RESEARCH | 3 tested (dollar), sisanya structural |
| Naive formation+RS BUY | REJECTED | lift 0.85x — no edge |

## Apa yang DILIHAT vs yang di BACKGROUND (sesuai permintaan lu)
**Ditampilkan (yang lu butuh buat tau arah):**
- Mission Control — regime, fear-greed, crash risk, valuation, top RS names
- Macro & Regime — cross-asset playbook, dollar hub, thesis library, playbook
- Early Warning — panic-bottom, crash lead-time, valuation room
- Decision — theme→best equity→beta chain→invalidation, shock→names, investment memos
- **Supply Chain** — photonics 12-layer bottleneck map, beta-play chains (primary→2nd→3rd order), market cap opportunity
- **Companies** — 68 nama kurasi by layer (★ conviction), catalyst timeline, institutional rotation, M&A watchlist, risk flags
- Knowledge Graph — shock propagation, typed edges
- Validation — status tiap sinyal (PRODUCTION/RESEARCH/REJECTED)

**Di background (kalkulasi, ga perlu diliat tiap saat):** walk-forward backtest, bootstrap significance,
surge-lift, permutation test — semua di `backtest.py` + `certify.py`. Jalanin `python certify.py` kalau
mau liat bukti validasi. Dashboard ga jalanin ini tiap render (biar cepat).

## Prinsip
- Production is earned — cuma yang lolos 4-fold gate jadi sinyal actionable.
- No number without a test. Ticker = Investment Memo (bukan watchlist). Decision-first.
- Jujur soal batas: crash ga bisa di-time (probabilistik); rotasi sektor ga prediktif; options/COT butuh data berbayar.

Detail angka: `research/RESEARCH_FINDINGS.md`. Spec lengkap: lihat versi arsip untuk MASTER_PRODUCT_SPEC.
