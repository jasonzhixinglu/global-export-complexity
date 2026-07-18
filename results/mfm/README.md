# Matrix factor model experiments

Bilateral-trade matrix factor models (Chen, Chen, Bolivar & Chen 2024 — see
`docs/references/`), one subdirectory per analysis. Each contains `summary.md`
(start here), figures, and `stats.json` with all estimates. Regenerate with
`python scripts/prototype_mfm.py [label ...]` after `python scripts/extract_ai_compute.py`.

| Analysis | Scope | World 2020-24 |
|---|---|---:|
| [847150_annual_2020_2024](847150_annual_2020_2024/summary.md) | HS 847150 ADP processing units / AI servers | $429B |
| [847180_annual_2020_2024](847180_annual_2020_2024/summary.md) | HS 847180 other ADP units / baseboards | $210B |
| [847330_annual_2020_2024](847330_annual_2020_2024/summary.md) | HS 847330 ADP parts / GPU cards | $593B |
| [ai_compute_annual_2020_2024](ai_compute_annual_2020_2024/summary.md) | Fed AI-compute basket (sum of the three) | $1,233B |
