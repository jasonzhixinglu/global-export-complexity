# Matrix factor model results

Bilateral-trade matrix factor models on the Fed AI-compute codes (847150 AI servers,
847180 baseboards/units, 847330 parts/GPU cards), per Chen, Chen, Bolivar & Chen
(2024) — see `docs/references/`. All estimation in $B dollar levels (logs bury scale).
Each analysis folder has `summary.md` (start here), figures, and `stats.json`.

```
annual/                constant-loading MFM on Atlas annual bilateral data, 2020-2024
  847150_2020_2024/  847180_2020_2024/  847330_2020_2024/  ai_compute_2020_2024/
  (regenerate: python scripts/prototype_mfm.py [label ...])

tvmfm/                 time-varying MFM on the monthly panel (results/panel_monthly)
  by_country/          12m trailing loadings, era-anchored hub labels
    847150/  847180/  847330/  ai_compute/
  chn_hkg_bloc/        same, with China+Hong Kong merged into one bloc (CHK);
    847150/ 847180/ 847330/ ai_compute/   entrepot churn cancels; TWN separate.
  chnhkg_usamex_blocs/  CHK and USA+MEX both merged (the only-tariff-break run)
    ai_compute/
  bandwidth_experiment/  OOS window-length comparison that chose the 12m window
  archive/
    ai_compute_chained/  superseded pre-anchoring run (chained label matching)
  (regenerate: python scripts/tvmfm_monthly_anchored.py [label ...];
   labels: 847150 847180 847330 ai_compute ai_compute_chnhkg 847150_chnhkg 847180_chnhkg 847330_chnhkg ai_compute_2blocs)
```

Headline findings so far: the parts network (847330) shows no structural breaks over
65 months while the systems layers reorganize repeatedly; at country level the
2023-07 break is the birth of a solo Taiwan hub; with CHN+HKG merged, only 2023-07
(Taiwan's rise) and 2025-04 (tariffs) survive as breaks — the 2024-10 country-level
burst was Hong Kong entrepot noise.
