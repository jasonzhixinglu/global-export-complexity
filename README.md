# global-export-complexity

Non-parametric analysis of global exports by **product complexity (PCI)**, country, and time,
using Harvard Growth Lab's *Atlas of Economic Complexity* HS92 HS4 trade data (2000–2024).

Two estimands, each with an explicit trade-accounting property:

1. **Distribution of export dollars across complexity** (value-weighted kernel density).
2. **A country's global market share as a function of complexity** (value-weighted *local-linear*
   regression — chosen over Nadaraya–Watson for lower boundary bias, and because it makes shares
   add up to exactly 100% across countries by construction).

See [`docs/analysis.md`](docs/analysis.md) for the full write-up — the core idea is how to
reconcile non-parametric smoothing with the accounting identities trade data must satisfy.

## Layout

```
src/gec/            importable package
  config.py         paths + analysis constants (YEARS, N_TOP, bandwidths, thresholds)
  data.py           load / clean / rank exporters / aggregate to product level
  estimators.py     local-linear shares, KDE, mass-conserving bins, calibration
  plotting.py       headless matplotlib helpers
scripts/            runnable entry points
  download_data.py    fetch raw CSV from Harvard Dataverse
  compute_surfaces.py compute & cache all surfaces -> data/derived/
  make_figures.py     render figures -> results/figures/
  run_diagnostics.py  conservation & adding-up checks -> figures + results/tables/
  run_all.py          the four steps above, in order
data/               git-ignored; raw/ (download) + derived/ (cached). See data/README.md
results/            committed outputs: figures/ and tables/
docs/               analysis.md — data, methodology, findings (single write-up)
legacy/             the original exploratory notebook (superseded)
```

## Setup & run

```bash
pip install -r requirements.txt
python scripts/run_all.py          # download (~430 MB) -> compute -> figures -> diagnostics
```

Steps are independent and idempotent; after the first download, re-run any single script.
Tune the analysis in `src/gec/config.py` (e.g. `N_TOP`, `COVER_THRESHOLDS`, bandwidths).

## Headline results

- **Estimators respect the accounting exactly.** Shares sum to 100% to machine precision; the
  dollar distribution conserves total mass exactly, with only mean-zero sub-range redistribution
  (not net bias). See [`docs/analysis.md`](docs/analysis.md).
- **Top-20 exporters cover ~72% of world trade on average**, but only ~45–50% at low complexity
  (commodities are exported by a long tail of economies). **Top-50 reaches ~93% overall** and
  clears 90% across nearly the whole complexity range except the extreme low tail.

Data provenance and the upstream harmonization that makes the accounting hold (BACI /
Bustos–Yildirim mirror reconciliation) are documented in [`docs/analysis.md`](docs/analysis.md)
(§2) and [`data/README.md`](data/README.md).
