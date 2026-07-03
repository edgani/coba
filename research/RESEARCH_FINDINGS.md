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

---

## 5. BISA NANGKEP PEMENANG SEBELUM LARI? (event study — jawaban pertanyaan SNDK/PLTR)

Pertanyaan lu: "SNDK/PLTR naik for a reason — bisa ga dapet SEBELUM surging, di harga berapa, kapan
keluar?" Gw uji di 482 nama S&P real 2013-2018 (PLTR/SNDK belum ada di era itu, tapi metodologinya yang
diuji — jalanin `run_research.py --tickers cache_lu.parquet` buat era mereka).

### Precision test — sinyal mana yang PUNYA edge nangkep surge (+30% dalam 63hr)?
Base rate random: 1.7%. LIFT = P(surge|sinyal) / P(surge|random).

| Sinyal | fires | hit rate | LIFT | verdict |
|---|---|---|---|---|
| formation + RS>0 (dashboard lama) | 203,827 | 1.5% | **0.85x** | ✗ lebih buruk dari random |
| 60d-high breakout + volume 1.5x | 8,678 | 1.3% | 0.76x | ✗ no edge |
| RS accelerating | 51,303 | 1.3% | 0.75x | ✗ no edge |
| tight-base breakout | 23,599 | 1.0% | 0.58x | ✗ no edge |
| near 52w-high + RS + volume | 11,477 | 1.0% | 0.56x | ✗ no edge |
| volume-spike 2x + uptrend | 4,534 | 1.7% | 1.01x | ✗ coin flip |
| **top-10% RS cross-sectional** | 55,354 | **3.6%** | **2.08x** | ✅ **EDGE** |

**Temuan besar:** SEMUA sinyal absolut (breakout, volume, base) = NOL edge. Cuma **cross-sectional RS
top-decile** yang punya tail edge (2x). Konsisten literatur momentum: ranking relatif jalan, breakout absolut engga.

### Entry/exit discipline (top-decile RS strategy) — jawaban "harga berapa masuk, kapan keluar"
Nama MASUK rekomendasi saat cross ke top-10% RS, KELUAR saat drop out. 907 trades, 55% win, avg hold 82hr.
Contoh REAL (entry→exit, harga+tanggal):

| ticker | masuk | harga | keluar | harga | return | hari |
|---|---|---|---|---|---|---|
| **AMD** | 2016-03-11 | $2.52 | 2017-06-12 | $12.09 | **+380%** | 458 |
| SWKS | 2014-02-10 | $30.70 | 2015-08-11 | $88.97 | +190% | 547 |
| AVGO | 2014-01-09 | $53.23 | 2015-08-11 | $124.21 | +133% | 579 |
| MU | 2016-08-10 | $14.20 | 2017-08-10 | $27.49 | +94% | 365 |

**YA — sistem nangkep AMD di $2.52 sebelum run 10x, dengan entry/exit konkret.** Ini yang lu mau.

### TAPI — apakah ini alpha teruji? BELUM (jujur)
Strategi 18%/thn vs benchmark 15%. Excess **p=0.41 (TIDAK signifikan)**, beta 0.86. Alpha +5%/thn TAPI
belum kebukti di 5 tahun. **Sebagian besar return = beta (market naik).** Top-decile RS punya tail edge
nyata (nangkep winners), tapi belum bisa diklaim alpha statistik di sample ini.

**Kesimpulan jujur buat "always be the winner":** mustahil. Yang realistis & sudah gw temukan: SATU sinyal
(cross-sectional RS top-decile) dengan tail edge yang nangkep pemenang besar. Basis ticker dashboard
HARUSNYA ini (ranking RS relatif), BUKAN formation+RS absolut (yang terbukti 0.85x = sampah). Entry =
masuk top-decile, exit = keluar. Alpha butuh validasi data lebih panjang (2008-2026 multi-regime).

## 6. BUBBLE / VALUASI EKSTREM — berapa lama & berapa room? (jawaban Bubble=100)

CAPE sekarang ~31 (persentil 95). Dari data 1871-2023:

| CAPE decile | fwd 1yr | fwd 3yr | fwd 5yr | maxDD 2yr |
|---|---|---|---|---|
| D0 (murah 5-9) | +15% | +36% | +80% | -7% |
| D9 (mahal 26-44) | +4% | +11% | +12% | -15% |

Saat CAPE setinggi sekarang: fwd 1yr +5%, 3yr +13%, **65% waktu tetap positif**, tapi maxDD 2yr -14%.
**Waktu dari CAPE>30 ke drawdown -20% berikutnya: median 21-26 BULAN** (min 0, max 62).

**Jawaban "Bubble=100, udah peak?": TIDAK berarti jual.** Valuasi ekstrem = return ke depan lebih kecil +
risiko ekor lebih tinggi, TAPI historis masih 2+ tahun room. Timing top mustahil. Bubble meter = ukuran
ROOM & RISIKO, bukan sinyal jual. Engine: `signal_edge.valuation_room()`.

⚠️ Bubble=100 di screenshot itu dari data SINTETIS sandbox — ga meaningful. Di data real lu, meter ini
harus dibaca sebagai konteks risiko (turunin size, siapin hedge), bukan trigger jual.

---

## 7. EARLY WARNING — panic bottom & euphoria top (TERUJI)

Pertanyaan lu: "early warning saat panic sell padahal mau bottom, & euforia padahal mau crash."
Diuji di S&P 500 + VIX real 2013-2018:

**PANIC = BOTTOM → SIGNIFIKAN & TERUJI:**
| sinyal | fwd 63d | vs baseline | p |
|---|---|---|---|
| VIX spike + oversold (z<-1) | +6.2% | +3.3% | <0.001 ✓ |
| breadth >80% below 50ma | +7.9% | +3.3% | ✓ |
| VIX vs 20d-avg (dose response) | spike +5.2% vs calm +2.1% | corr +0.24 | <0.0001 ✓ |
| composite fear-greed (EXTREME FEAR) | +5.3% | — | corr(greed,fwd) -0.21, p<0.0001 ✓ |

**PANIC selling MEMANG sinyal beli kontrarian dengan edge signifikan.** Ini di dashboard sekarang
(`early_warning.py` → Today's Attention: "⚠ PANIC BOTTOM setup" saat aktif).

**EUPHORIA = TOP → LEMAH, belum terbukti:** fwd return sedikit lebih rendah tapi p=0.34 (tidak
signifikan) di 2013-18 (bias bull market). Butuh data 2008/2020/2022. Di-FLAG jujur, ga di-overclaim.

## 8. CONNECTING THE DOTS (lead-lag) — jujur: prediktif LEMAH

Pertanyaan lu: "NVDA surging → supplier CPO/photonic ikut? oil→tanker→dst?" Diuji:
- Pair supply-chain terkenal (NVDA→AMD, NVDA→MU, AAPL→SWKS): **TIDAK ada lead-lag prediktif signifikan.**
- Scan sistematis: cuma pair spurious lemah (ga ada logika ekonomi).

**Kesimpulan jujur:** "dots" MEMANG nyambung, tapi **contemporaneous (bareng), bukan prediktif** — market
pricing in same-day, ga bisa front-run harian. Jadi beta-chain berguna buat **thematic exposure** ("kalo
tema X lari, nama-nama ini ikut" → own the chain), BUKAN buat prediksi lag. Propagasi fundamental
(earnings NVDA → supplier next quarter) plausible tapi butuh data fundamental yang belum ada. Klaim
"dashboard bisa prediksi urutan surging dari lead-lag harian" = TIDAK didukung data. Gw ga akan jual itu.

## OTOMASI PENUH (lu ga perlu jalanin apa-apa)

`python certify.py` → jalanin SEMUA test di atas otomatis, hasilkan `CERTIFICATION.md` dengan status
PRODUCTION/RESEARCH/FAIL per engine + confidence. Lu ga perlu ngerti test-nya — statusnya jelas.
`python warroom/data_ingest.py` (via ensure/add_ticker) → auto-tarik ticker baru ke cache (jalan di
mesin lu dengan yfinance/stooq; di sandbox ke-block, gagal graceful).
