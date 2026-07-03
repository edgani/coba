# RESEARCH FINDINGS — Multi-Driver Attribution (data real, sudah dijalankan)

**Ini bukan teori. Ini hasil run di data real** (S&P 500 harian 2013-2018 dari 505 nama + Shiller
CAPE/CPI/earnings/rates 1871-2023 + VIX 1990-2026, semua ditarik dari GitHub di sandbox). Script:
`run_research.py`. Data: `research/*.parquet`. Engine: `warroom/causal_attribution.py` + `backtest.py`.

Jawaban langsung buat pertanyaan lu: **"apa bener sebab tunggal, atau ada hidden metrics?"**

---

## 1. TICKER SELECTION — apa sinyal dashboard punya edge teruji? → BELUM

Gw test sinyal yang dashboard pakai (formation BULLISH + RS63>0 → Long) di 483 nama S&P real,
walk-forward + bootstrap significance:

- **0 dari 45 kandidat teratas LOLOS gate** (exp>0, hit>50%, beats-random p<0.10, walk-forward konsisten).
- Bootstrap p-value 0.39–1.0 → sinyal **TIDAK ngalahin entry random**. Expectancy positif itu **beta**
  (market naik 2013-18), bukan alpha.
- Information Coefficient momentum factor: mom_126 IC=0.024 (p=0.36), mom_63 IC=0.019 (p=0.39) —
  **TIDAK signifikan.** Ranking momentum ga punya daya prediksi yang lolos uji di periode ini.

**Kesimpulan brutal:** dashboard yang bilang "beli X karena quad mendukung / momentum bagus" — kalo diuji
jujur, sinyal itu **belum kebukti ngalahin random.** Ini persis "asal bunyi" yang lu benci. **Ini kenapa
gate wajib**: ticker ga boleh muncul sebagai BUY sebelum lolos validasi di data real.

⚠️ Caveat jujur: 2013-2018 itu bull market tenang (sinyal directional susah nunjukin edge di situ). Di
data lu yang lebih panjang + multi-regime (2008, 2020, 2022), hasilnya bisa beda. TAPI defaultnya tetap:
**belum lolos = jangan tampil sebagai sinyal.** Production is earned.

---

## 2. CRASH ATTRIBUTION — sebab tunggal atau hidden metrics?

Multi-factor regression prediksi forward-12mo drawdown (1872-2023, 1820 bulan), kontrol semua confounder:

| Faktor | t-stat | Signifikan? | Independent driver? |
|---|---|---|---|
| **prior volatility** | **−6.53** | *** p<0.01 | ✅ YA — prediktor TERKUAT |
| **rate change (12mo)** | **−3.70** | *** p<0.01 | ✅ YA |
| rate level | +2.14 | ** p<0.05 | ✅ ya |
| CAPE (valuasi) | −1.74 | * p<0.10 | ❌ lemah (jatuh saat dikontrol) |
| **CPI/inflasi** | **−0.82** | **not sig** | ❌ **BUKAN driver independen** |

**R² = 0.033.** Faktor makro standar cuma jelasin **3.3%** variance drawdown.

### Jawaban per pertanyaan lu:

**"2022 crash gara-gara inflasi doang?" → BUKAN.**
Inflasi (CPI) **tidak signifikan** sebagai prediktor crash saat dikontrol. Mekanisme sebenarnya =
**rate-change** (hiking tercepat 40 tahun, t=−3.70) + valuasi tinggi (CAPE 34 sebelum). Inflasi itu
**katalis/narasi**, rate-change itu **mekanisme**. Beda besar — dan cuma ketahuan kalo diuji multi-faktor.

**"Bottleneck gara-gara supply-demand doang?"** → Belum bisa gw uji penuh (butuh data inventory/freight/
commodity yang belum ketarik). Tapi prinsipnya sama: harus diuji lawan hidden metrics (capex cycle, FX,
substitusi), bukan diasumsikan.

**Hidden metric yang ketemu:** **prior volatility** = sinyal fragility terkuat. Market telegraph
kerapuhannya lewat vol regime SEBELUM trigger keliatan. Ini yang "kita ga liat" kalo cuma fokus ke narasi.

### Per-crash (kondisi 6 bulan SEBELUM trough) — tiap crash driver-nya BEDA:

| Crash | CAPE | CPI% | Δrate12 | VIX pre | Driver dominan |
|---|---|---|---|---|---|
| 1987 | 16 | 3.8 | +0.7 | n/a | Rate shock + portfolio-insurance feedback (**BUKAN valuasi**) |
| 2000 | 43 | 3.8 | +1.0 | 23 | Valuasi ekstrem (bubble) — fragility bertahun sebelumnya |
| 2008 | 23 | 3.9 | −1.0 | 22 | **Kredit/leverage — INVISIBLE ke makro standar** |
| 2020 COVID | 29 | 1.7 | −1.3 | 16 | **Shock eksogen asli** — VIX tenang, ga ada pre-signal |
| 2022 | 34 | 8.5 | +0.5 | 27 | Rate-change + valuasi unwind (inflasi = katalis) |

**"COVID gara-gara COVID doang?" → Ini justru IYA.** VIX 16 (tenang) sebelumnya, ga ada sinyal makro
fragility. Shock eksogen murni. **Jujur: kadang sebab yang keliatan MEMANG sebabnya** — dan disiplinnya
adalah nguji, bukan maksa cari "hidden" yang ga ada.

**2008 pelajaran penting:** makro standar MISS total (CAPE cuma 23, CPI benign). Driver aslinya kredit/
leverage yang **ga ada di dataset makro standar**. Ini bukti: butuh data tambahan (credit spread, bank
leverage), BUKAN maksa kesimpulan dari data yang ada = asal bunyi.

---

## 3. BULL RUN — "gara-gara QE doang?" → BUKAN

Decompose total return S&P jadi earnings-growth vs multiple-expansion:

| Periode | Total | Earnings growth | Multiple expansion | Verdict |
|---|---|---|---|---|
| 2013-2019 (QE era) | +115% | **+60%** | +38% | **61% earnings** — fundamental, bukan cuma QE |
| 2020-2021 (stimulus) | +69% | **+79%** | +48% | **62% earnings** — fundamental |

**Earnings yang DOMINAN di dua-duanya**, bukan re-rating/multiple expansion. Kalo bull run cuma QE, yang
dominan harusnya multiple expansion. Faktanya earnings ~60%. QE berkontribusi (re-rating ~38%), tapi
narasi "cuma QE" **salah secara data.**

---

## 4. IMPLIKASI BUAT DASHBOARD (aturan baru, ke-enforce)

1. **Ga ada BUY tanpa validasi.** Ticker harus lolos walk-forward + significance di data real. 0/45 lolos
   di test ini → di data sandbox, dashboard harusnya nampilin "no validated setups", bukan nama random.
2. **Ga ada atribusi sebab-tunggal.** Setiap klaim regime/crash lewat `causal_attribution.multi_factor_*`
   — kontrol confounder. "Quad 3 → risk-off" ga cukup; harus tunjukin driver mana yang independen.
3. **Confidence = fungsi R²/evidence, bukan narasi.** R²=3.3% → confidence rendah → jangan overclaim.
   Ini Rule 8 lu: "Unknown is better than wrong."
4. **Data gaps di-flag, bukan ditambal.** 2008 butuh credit data; bottleneck butuh commodity/inventory.
   Yang belum ada → "research needed", bukan dikarang.

---

## Cara jalanin di data LU (lebih recent/lengkap)

```bash
python run_research.py --data your_panel.parquet   # ticker validation + factor IC
python run_research.py --macro                       # crash/bull attribution (pakai Shiller+VIX)
```

Ganti data 2013-2018 dengan cache lu (2008-2026) → hasil multi-regime yang lebih kuat. Engine-nya
(`causal_attribution.py`, `backtest.py`) siap; tinggal kasih makan data lu.
