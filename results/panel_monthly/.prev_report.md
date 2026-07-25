# Monthly bilateral supply-chain panel — build report

60 HS6 codes (stages 1-8, docs/data.md); 30 countries + ROW; 2017-01 .. 2026-04 (balanced endpoint = slowest reporter).
Sources: UN Comtrade monthly (backbone) + TDM (TWN always; CHN/VNM beyond Comtrade). Reconciliation: Growth Lab mirroring (Bustos-Yildirim et al., GL WP 251) — gravity-estimated CIF/FOB ratios (capped 1.20), network-estimated annual reliability scores, softmax pair weights with bottom-decile disregard; see script docstring for the faithful-implementation notes.

- Rows: 3,501,118; total value 13715B (by year, $B: 2017 965, 2018 1182, 2019 1161, 2020 1269, 2021 1576, 2022 1535, 2023 1357, 2024 1613, 2025 2054, 2026 1003)
- Provenance shares: both:comtrade+comtrade 54.7%, m_only:comtrade 21.4%, x_only:comtrade 15.7%, both:tdm+comtrade 3.4%, both:comtrade+tdm 2.8%, m_only:tdm 1.2%, x_only:tdm 0.7%, both:tdm+tdm 0.2%
- Mirror gap log(x/m_fob), cells with both sides: median +0.093, IQR 1.912 (2,137,539 cells)

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

- Mirror-fallback set: ESP, FRA, IND, ITA, PHL, SWE -> balanced endpoint 2026-04; dark-cell share 0.20% of monthly value.
- Cost of pushing further (dark share if all countries reporting before that month were mirrored):
  - endpoint 2026-03: fallback 1 countries (FRA), dark 0.01%
  - endpoint 2026-04: fallback 6 countries (ESP, FRA, IND, ITA, PHL, SWE), dark 0.20%
  - endpoint 2026-05: fallback 13 countries (BEL, ESP, FRA, HUN, IND, IRL, ITA, MYS...), dark 2.55%
  - endpoint 2026-06: fallback 27 countries (BEL, CAN, CHE, CZE, DEU, DNK, ESP, FRA...), dark 32.98%
- Re-running the fetch scripts + assembler rolls the endpoint forward as laggards file; the fallback set should be revisited then.

## Validation vs Atlas annual bilateral (2017–2024, kept-kept corridors > $0.1M)

| code | corridor-years | log-corr | median panel/Atlas | IQR(log ratio) |
|---|---|---|---|---|
| 252800 | 147 | 0.967 | 1.04 | 0.26 |
| 280421 | 654 | 0.970 | 1.10 | 0.28 |
| 280429 | 1482 | 0.931 | 1.12 | 0.44 |
| 280461 | 922 | 0.981 | 1.04 | 0.31 |
| 280480 | 172 | 0.966 | 1.10 | 0.25 |
| 281000 | 644 | 0.940 | 1.10 | 0.25 |
| 282560 | 917 | 0.921 | 1.06 | 0.42 |
| 283325 | 1111 | 0.968 | 1.09 | 0.30 |
| 284011 | 180 | 0.984 | 1.10 | 0.20 |
| 284019 | 426 | 0.978 | 1.07 | 0.27 |
| 284920 | 1372 | 0.971 | 1.08 | 0.31 |
| 285000 | 1449 | 0.962 | 1.03 | 0.31 |
| 370130 | 1867 | 0.960 | 1.03 | 0.36 |
| 370199 | 837 | 0.932 | 1.05 | 0.39 |
| 370790 | 2653 | 0.952 | 1.02 | 0.41 |
| 381800 | 2784 | 0.963 | 1.05 | 0.34 |
| 811292 | 1022 | 0.905 | 1.07 | 0.37 |
| 811299 | 870 | 0.924 | 1.02 | 0.36 |
| 841459 | 5467 | 0.954 | 1.05 | 0.39 |
| 841950 | 4908 | 0.960 | 1.05 | 0.39 |
| 842129 | 4683 | 0.951 | 1.05 | 0.41 |
| 842139 | 5431 | 0.957 | 1.04 | 0.42 |
| 842199 | 5768 | 0.956 | 1.06 | 0.42 |
| 847150 | 5833 | 0.947 | 1.06 | 0.49 |
| 847180 | 5489 | 0.927 | 1.02 | 0.55 |
| 847330 | 6376 | 0.946 | 1.01 | 0.54 |
| 848610 | 1388 | 0.908 | 1.14 | 0.55 |
| 848620 | 3173 | 0.915 | 1.08 | 0.48 |
| 848630 | 719 | 0.918 | 1.05 | 0.38 |
| 848640 | 2623 | 0.933 | 1.11 | 0.47 |
| 848690 | 3845 | 0.948 | 1.10 | 0.57 |
| 852351 | 5018 | 0.908 | 1.02 | 0.61 |
| 852352 | 4172 | 0.912 | 1.06 | 0.46 |
| 852359 | 2435 | 0.890 | 1.01 | 0.47 |
| 853290 | 1538 | 0.923 | 1.04 | 0.37 |
| 853390 | 1500 | 0.905 | 1.03 | 0.40 |
| 854110 | 4111 | 0.930 | 1.05 | 0.55 |
| 854121 | 2680 | 0.895 | 1.02 | 0.58 |
| 854129 | 4266 | 0.911 | 1.05 | 0.63 |
| 854130 | 2188 | 0.910 | 1.04 | 0.44 |
| 854160 | 3424 | 0.940 | 1.04 | 0.42 |
| 854190 | 3077 | 0.917 | 1.05 | 0.60 |
| 854231 | 6197 | 0.920 | 1.03 | 0.70 |
| 854232 | 4407 | 0.949 | 1.20 | 0.57 |
| 854233 | 3543 | 0.854 | 1.03 | 0.58 |
| 854239 | 6008 | 0.930 | 1.07 | 0.70 |
| 854290 | 4055 | 0.855 | 1.04 | 0.77 |
| 900120 | 1001 | 0.972 | 1.01 | 0.41 |
| 900190 | 3863 | 0.959 | 1.00 | 0.39 |
| 900219 | 2484 | 0.943 | 1.01 | 0.49 |
| 900220 | 1992 | 0.859 | 1.03 | 0.41 |
| 900290 | 3093 | 0.924 | 1.02 | 0.52 |
| 900699 | 1402 | 0.799 | 1.02 | 0.51 |
| 901210 | 2017 | 0.933 | 1.16 | 0.46 |
| 901290 | 2023 | 0.949 | 1.06 | 0.43 |
| 903082 | 2831 | 0.941 | 1.02 | 0.50 |
| 903084 | 2561 | 0.918 | 1.02 | 0.44 |
| 903141 | 1794 | 0.960 | 1.13 | 0.52 |
| 903300 | 4224 | 0.881 | 1.04 | 0.68 |

_Generated by `scripts/build_monthly_panel.py`; panel parquet in `data/derived/` (git-ignored)._