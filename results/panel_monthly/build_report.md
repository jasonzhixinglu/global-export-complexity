# Monthly bilateral supply-chain panel — build report

60 HS6 codes (stages 1-8, docs/data.md); 30 countries + ROW; 2017-01 .. 2026-04 (balanced endpoint = slowest reporter).
Sources: UN Comtrade monthly (backbone) + TDM (TWN always; CHN/VNM beyond Comtrade). Reconciliation: Growth Lab mirroring (Bustos-Yildirim et al., GL WP 251) — gravity-estimated CIF/FOB ratios (capped 1.20), network-estimated annual reliability scores, softmax pair weights with bottom-decile disregard; see script docstring for the faithful-implementation notes.

- Rows: 3,501,118; total value 14985B (by year, $B: 2017 1045, 2018 1189, 2019 1193, 2020 1299, 2021 1605, 2022 1728, 2023 1565, 2024 1815, 2025 2428, 2026 1119)
- Provenance shares: both:comtrade+comtrade 54.7%, m_only:comtrade 21.4%, x_only:comtrade 15.7%, both:tdm+comtrade 3.4%, both:comtrade+tdm 2.8%, m_only:tdm 1.2%, x_only:tdm 0.7%, both:tdm+tdm 0.2%
- Mirror gap log(x/m_fob), cells with both sides: median +0.077, IQR 1.937 (2,137,539 cells)

## Reporter horizons (last reported month)

| country | last period |
|---|---|
| FRA | 2025-12 |
| PHL | 2026-03 |
| IND | 2026-03 |
| ITA | 2026-03 |
| ESP | 2026-03 |
| SWE | 2026-03 |
| VNM | 2026-04 |
| MYS | 2026-04 |
| NLD | 2026-04 |
| HUN | 2026-04 |
| POL | 2026-04 |
| IRL | 2026-04 |
| BEL | 2026-04 |
| USA | 2026-05 |
| MEX | 2026-05 |
| HKG | 2026-05 |
| SGP | 2026-05 |
| THA | 2026-05 |
| DEU | 2026-05 |
| CZE | 2026-05 |
| JPN | 2026-05 |
| IDN | 2026-05 |
| CAN | 2026-05 |
| GBR | 2026-05 |
| CHE | 2026-05 |
| DNK | 2026-05 |
| ISR | 2026-05 |
| CHN | 2026-06 |
| TWN | 2026-06 |
| KOR | 2026-06 |

## Publication lags and the endpoint choice

National monthly submissions arrive with heterogeneous lags (~2-4 months; France has stopped monthly reporting since 2025-12 and its TDM edition is inaccessible). The balanced endpoint is the last month at which every kept country outside the mirror-fallback set has reported. Fallback countries stay covered on corridors where the partner reports; only laggard-laggard and laggard-ROW corridors go dark (set to 0, weighted share of 2025+ value shown below).

- Mirror-fallback set: ESP, FRA, IND, ITA, PHL, SWE -> balanced endpoint 2026-04; dark-cell share 0.49% of monthly value.
- Cost of pushing further (dark share if all countries reporting before that month were mirrored):
  - endpoint 2026-03: fallback 1 countries (FRA), dark 0.09%
  - endpoint 2026-04: fallback 6 countries (ESP, FRA, IND, ITA, PHL, SWE), dark 0.49%
  - endpoint 2026-05: fallback 13 countries (BEL, ESP, FRA, HUN, IND, IRL, ITA, MYS...), dark 3.39%
  - endpoint 2026-06: fallback 27 countries (BEL, CAN, CHE, CZE, DEU, DNK, ESP, FRA...), dark 33.65%
- Re-running the fetch scripts + assembler rolls the endpoint forward as laggards file; the fallback set should be revisited then.

## Validation vs Atlas annual bilateral (2017–2024, kept-kept corridors > $0.1M)

Log-based columns treat every corridor equally (they overstate small linkages); the value-weighted columns are dominated by the large corridors the analysis actually rides on.

| code | corridor-years | log-corr | median ratio | IQR(log) | aggregate ratio | value-wtd within ±25% | value-wtd MAPE |
|---|---|---|---|---|---|---|---|
| 252800 | 149 | 0.987 | 1.04 | 0.20 | 1.11 | 83% | 14% |
| 280421 | 659 | 0.990 | 1.05 | 0.15 | 1.05 | 94% | 9% |
| 280429 | 1493 | 0.962 | 1.09 | 0.25 | 1.14 | 88% | 17% |
| 280461 | 923 | 0.989 | 1.10 | 0.20 | 1.10 | 87% | 12% |
| 280480 | 175 | 0.973 | 1.09 | 0.19 | 1.10 | 82% | 14% |
| 281000 | 652 | 0.958 | 1.08 | 0.19 | 1.11 | 91% | 14% |
| 282560 | 921 | 0.955 | 1.10 | 0.22 | 1.17 | 84% | 19% |
| 283325 | 1111 | 0.984 | 1.11 | 0.21 | 1.09 | 90% | 11% |
| 284011 | 179 | 0.984 | 1.09 | 0.23 | 1.07 | 93% | 12% |
| 284019 | 435 | 0.986 | 1.08 | 0.18 | 1.11 | 94% | 13% |
| 284920 | 1381 | 0.985 | 1.10 | 0.21 | 1.10 | 92% | 11% |
| 285000 | 1467 | 0.977 | 1.09 | 0.19 | 1.09 | 93% | 11% |
| 370130 | 1867 | 0.985 | 1.07 | 0.16 | 1.06 | 95% | 9% |
| 370199 | 847 | 0.983 | 1.08 | 0.18 | 1.06 | 90% | 11% |
| 370790 | 2678 | 0.984 | 1.07 | 0.17 | 1.06 | 92% | 10% |
| 381800 | 2795 | 0.974 | 1.09 | 0.19 | 0.99 | 86% | 15% |
| 811292 | 1023 | 0.925 | 1.09 | 0.23 | 1.02 | 68% | 36% |
| 811299 | 874 | 0.963 | 1.09 | 0.23 | 1.12 | 85% | 16% |
| 841459 | 5500 | 0.986 | 1.10 | 0.18 | 1.06 | 93% | 11% |
| 841950 | 4925 | 0.983 | 1.10 | 0.19 | 1.06 | 95% | 9% |
| 842129 | 4701 | 0.982 | 1.10 | 0.18 | 1.07 | 94% | 10% |
| 842139 | 5443 | 0.982 | 1.09 | 0.21 | 0.90 | 72% | 19% |
| 842199 | 5779 | 0.986 | 1.09 | 0.18 | 1.05 | 94% | 9% |
| 847150 | 5845 | 0.979 | 1.11 | 0.22 | 1.07 | 93% | 11% |
| 847180 | 5507 | 0.973 | 1.11 | 0.21 | 1.19 | 84% | 23% |
| 847330 | 6398 | 0.986 | 1.09 | 0.21 | 1.11 | 85% | 20% |
| 848610 | 1388 | 0.933 | 1.16 | 0.36 | 1.16 | 88% | 19% |
| 848620 | 3178 | 0.927 | 1.10 | 0.31 | 0.98 | 81% | 18% |
| 848630 | 722 | 0.929 | 1.10 | 0.27 | 0.99 | 80% | 19% |
| 848640 | 2628 | 0.948 | 1.13 | 0.33 | 1.09 | 69% | 23% |
| 848690 | 3863 | 0.980 | 1.11 | 0.21 | 1.05 | 93% | 10% |
| 852351 | 5068 | 0.970 | 1.10 | 0.19 | 1.18 | 75% | 23% |
| 852352 | 4208 | 0.966 | 1.10 | 0.20 | 1.09 | 89% | 14% |
| 852359 | 2468 | 0.960 | 1.09 | 0.20 | 1.12 | 86% | 18% |
| 853290 | 1555 | 0.981 | 1.10 | 0.21 | 1.09 | 86% | 16% |
| 853390 | 1543 | 0.973 | 1.07 | 0.17 | 1.11 | 89% | 16% |
| 854110 | 4154 | 0.987 | 1.09 | 0.19 | 1.16 | 83% | 22% |
| 854121 | 2731 | 0.977 | 1.09 | 0.19 | 1.16 | 90% | 21% |
| 854129 | 4304 | 0.975 | 1.10 | 0.18 | 1.13 | 88% | 18% |
| 854130 | 2226 | 0.971 | 1.08 | 0.18 | 1.07 | 93% | 13% |
| 854160 | 3457 | 0.986 | 1.09 | 0.17 | 1.14 | 88% | 18% |
| 854190 | 3118 | 0.966 | 1.09 | 0.20 | 1.10 | 79% | 23% |
| 854231 | 6216 | 0.983 | 1.12 | 0.19 | 1.16 | 81% | 22% |
| 854232 | 4433 | 0.986 | 1.30 | 0.19 | 1.32 | 59% | 32% |
| 854233 | 3580 | 0.948 | 1.10 | 0.21 | 1.26 | 85% | 32% |
| 854239 | 6025 | 0.983 | 1.11 | 0.20 | 1.21 | 75% | 24% |
| 854290 | 4089 | 0.953 | 1.10 | 0.21 | 1.21 | 79% | 24% |
| 900120 | 1021 | 0.992 | 1.08 | 0.18 | 1.12 | 84% | 14% |
| 900190 | 3895 | 0.991 | 1.10 | 0.17 | 1.09 | 93% | 13% |
| 900219 | 2536 | 0.981 | 1.10 | 0.20 | 1.09 | 82% | 14% |
| 900220 | 2040 | 0.966 | 1.08 | 0.17 | 1.12 | 86% | 16% |
| 900290 | 3137 | 0.974 | 1.09 | 0.18 | 1.11 | 88% | 14% |
| 900699 | 1454 | 0.935 | 1.05 | 0.17 | 1.20 | 86% | 25% |
| 901210 | 2016 | 0.951 | 1.12 | 0.28 | 1.18 | 84% | 20% |
| 901290 | 2037 | 0.981 | 1.09 | 0.18 | 1.08 | 89% | 11% |
| 903082 | 2849 | 0.954 | 1.09 | 0.28 | 1.03 | 74% | 20% |
| 903084 | 2603 | 0.965 | 1.10 | 0.22 | 1.15 | 82% | 18% |
| 903141 | 1799 | 0.971 | 1.14 | 0.32 | 1.17 | 77% | 19% |
| 903300 | 4283 | 0.974 | 1.09 | 0.18 | 1.11 | 87% | 15% |
| **ALL** | 164351 | 0.977 | 1.10 | 0.21 | 1.16 | 79% | 22% |

_Generated by `scripts/build_monthly_panel.py`; panel parquet in `data/derived/` (git-ignored)._