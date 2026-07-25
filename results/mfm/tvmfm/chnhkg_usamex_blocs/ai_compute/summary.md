# Era-anchored time-varying MFM — AI compute, CHN+HKG and USA+MEX blocs, monthly panel

12m trailing loadings, k=r=4, $B levels; months aligned to per-era constant anchors (Procrustes), no chained matching. In-sample R^2 0.982; mean within-era loading step 0.074 (superseded chained version: ../archive/ai_compute_chained).

## Era 0: 2017-12 .. 2019-03

- export hub 1 (CHK-led, serves USM-hub): CHK +5.37, MYS +0.36, CAN +0.13, USM -0.10, TWN +0.08, NLD -0.06
- export hub 2 (KOR-led, serves CHK-hub): KOR +4.38, TWN +2.94, SGP +0.64, THA +0.48, USM -0.39, MYS +0.36
- export hub 3 (USM-led, serves CAN-hub): USM +4.71, MYS +2.17, SGP +0.80, TWN +0.69, NLD -0.49, KOR -0.42
- export hub 4 (NLD-led, serves ROW-hub): NLD +3.10, CZE +2.76, DEU +2.07, USM +1.42, MYS -1.38, KOR +0.87

## Era 1: 2019-04 .. 2019-11

- export hub 1 (CHK-led, serves USM-hub): CHK +5.25, TWN +0.96, KOR -0.55, MYS +0.30, CAN +0.19, SGP +0.17
- export hub 2 (TWN-led, serves CHK-hub): TWN +3.84, KOR +3.57, SGP +0.55, THA +0.55, MYS +0.50, CZE -0.39
- export hub 3 (USM-led, serves CAN-hub): USM +5.11, MYS +1.16, SGP +0.69, KOR +0.64, TWN -0.45, DEU +0.33
- export hub 4 (CZE-led, serves DEU-hub): CZE +3.58, NLD +2.85, DEU +1.46, KOR +1.43, HUN +0.87, IRL +0.81

## Era 2: 2019-12 .. 2020-11

- export hub 1 (CHK-led, serves USM-hub): CHK +5.29, NLD +0.54, CZE +0.49, DEU +0.31, KOR -0.27, POL +0.25
- export hub 2 (TWN-led, serves USM-hub): TWN +4.72, KOR +1.51, MYS +1.16, CZE -0.95, NLD -0.81, USM +0.58
- export hub 3 (USM-led, serves ROW-hub): USM +5.00, DEU +0.92, NLD +0.88, CZE +0.88, MYS +0.74, SGP +0.52
- export hub 4 (KOR-led, serves USM-hub): KOR +4.43, CZE +1.75, NLD +1.66, MYS -0.86, DEU +0.71, VNM +0.63

## Era 3: 2020-12 .. 2022-02

- export hub 1 (CHK-led, serves USM-hub): CHK +5.34, ROW +0.41, MYS +0.36, THA -0.28, SGP +0.23, CZE -0.20
- export hub 2 (TWN-led, serves USM-hub): TWN +4.37, KOR +2.70, VNM +1.28, MYS +0.71, THA +0.52, USM -0.36
- export hub 3 (USM-led, serves ROW-hub): USM +4.92, ROW +1.27, SGP +0.97, KOR -0.68, THA +0.62, NLD -0.60
- export hub 4 (NLD-led, serves ROW-hub): NLD +2.85, CZE +2.67, DEU +2.15, ROW -1.81, USM +1.24, GBR +0.89

## Era 4: 2022-03 .. 2022-09

- export hub 1 (CHK-led, serves USM-hub): CHK +5.34, KOR +0.28, DEU +0.27, MYS +0.23, ROW +0.22, SGP +0.22
- export hub 2 (TWN-led, serves USM-hub): TWN +5.29, KOR +0.76, ROW -0.40, MYS +0.26, SGP -0.25, VNM -0.25
- export hub 3 (USM-led, serves ROW-hub): USM +5.02, CZE +0.94, VNM +0.81, NLD +0.67, KOR -0.66, DEU +0.59
- export hub 4 (VNM-led, serves USM-hub): VNM -4.11, KOR -3.07, MYS -1.21, SGP -0.59, ROW -0.55, THA -0.43

## Era 5: 2022-10 .. 2025-03

- export hub 1 (CHK-led, serves USM-hub): CHK +5.32, NLD +0.49, DEU +0.40, MYS +0.28, CZE +0.26, HUN +0.17
- export hub 2 (TWN-led, serves USM-hub): TWN +5.36, KOR +0.38, MYS +0.19, VNM -0.16, THA +0.13, SGP +0.06
- export hub 3 (USM-led, serves ROW-hub): USM +5.11, SGP +1.57, CZE +0.34, KOR -0.24, HUN +0.24, MYS +0.23
- export hub 4 (VNM-led, serves CHK-hub): VNM -4.38, KOR -2.78, MYS -1.09, THA -0.75, SGP -0.44, JPN -0.20

## Era 6: 2025-04 .. 2026-04

- export hub 1 (CHK-led, serves ROW-hub): CHK +3.97, USM +3.41, CZE +0.57, MYS +0.53, NLD +0.47, VNM +0.41
- export hub 2 (TWN-led, serves USM-hub): TWN +5.37, CHK +0.21, KOR +0.16, MYS +0.16, VNM -0.13, USM -0.12
- export hub 3 (SGP-led, serves TWN-hub): SGP +5.36, KOR +0.29, VNM -0.19, USM +0.19, CZE -0.17, NLD -0.14
- export hub 4 (KOR-led, serves USM-hub): KOR -4.31, VNM -3.09, THA -0.71, PHL -0.44, USM +0.28, MYS -0.20

## Cross-era hub crosswalk (|cosine| between anchor loadings, rows = earlier era hub, cols = later era hub)

### era 0 -> era 1

| | hub 1' | hub 2' | hub 3' | hub 4' |
|---|---|---|---|---|
| hub 1 | 0.98 | 0.05 | 0.01 | 0.01 |
| hub 2 | 0.01 | 0.97 | 0.01 | 0.10 |
| hub 3 | 0.04 | 0.06 | 0.93 | 0.20 |
| hub 4 | 0.01 | 0.08 | 0.23 | 0.93 |

### era 1 -> era 2

| | hub 1' | hub 2' | hub 3' | hub 4' |
|---|---|---|---|---|
| hub 1 | 0.97 | 0.21 | 0.01 | 0.14 |
| hub 2 | 0.13 | 0.87 | 0.15 | 0.44 |
| hub 3 | 0.01 | 0.13 | 0.92 | 0.02 |
| hub 4 | 0.17 | 0.28 | 0.23 | 0.72 |

### era 2 -> era 3

| | hub 1' | hub 2' | hub 3' | hub 4' |
|---|---|---|---|---|
| hub 1 | 0.98 | 0.05 | 0.05 | 0.18 |
| hub 2 | 0.10 | 0.91 | 0.22 | 0.18 |
| hub 3 | 0.03 | 0.13 | 0.87 | 0.44 |
| hub 4 | 0.07 | 0.35 | 0.20 | 0.51 |

### era 3 -> era 4

| | hub 1' | hub 2' | hub 3' | hub 4' |
|---|---|---|---|---|
| hub 1 | 0.99 | 0.01 | 0.02 | 0.01 |
| hub 2 | 0.01 | 0.87 | 0.05 | 0.47 |
| hub 3 | 0.02 | 0.05 | 0.89 | 0.01 |
| hub 4 | 0.12 | 0.04 | 0.42 | 0.11 |

### era 4 -> era 5

| | hub 1' | hub 2' | hub 3' | hub 4' |
|---|---|---|---|---|
| hub 1 | 1.00 | 0.00 | 0.01 | 0.00 |
| hub 2 | 0.00 | 0.99 | 0.02 | 0.02 |
| hub 3 | 0.02 | 0.02 | 0.95 | 0.06 |
| hub 4 | 0.01 | 0.02 | 0.02 | 0.99 |

### era 5 -> era 6

| | hub 1' | hub 2' | hub 3' | hub 4' |
|---|---|---|---|---|
| hub 1 | 0.75 | 0.04 | 0.00 | 0.03 |
| hub 2 | 0.02 | 1.00 | 0.02 | 0.03 |
| hub 3 | 0.62 | 0.02 | 0.32 | 0.08 |
| hub 4 | 0.03 | 0.02 | 0.08 | 0.91 |

## Figures

![drift](drift.png)
![export loadings](loadings_export.png)
![import loadings](loadings_import.png)
![factors](factors.png)

_Generated by `scripts/tvmfm_monthly_anchored.py`._