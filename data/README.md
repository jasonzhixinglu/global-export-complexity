# Data

> **See [docs/data.md](../docs/data.md)** — the master reference for all
> sources, panels, taxonomy, and licensing. This file documents only the Atlas
> raw download below.

This directory is **git-ignored** (see `.gitignore`). Nothing here is committed; regenerate it
with `python scripts/download_data.py`.

```
data/
  raw/        hs92_country_product_year_4.csv   (downloaded, ~430 MB)
  derived/    surfaces.npz, dist_diag.npz, meta.json   (built by compute_surfaces.py)
```

## Source

Harvard Growth Lab — **The Atlas of Economic Complexity**, HS92 International Trade Data at the
HS4 (4-digit) `country × product × year` level.

- Dataverse: <https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/T4CHWJ>
- DOI: `doi:10.7910/DVN/T4CHWJ` · dataset **version 18**, released **2026-04-22**
- File: `hs92_country_product_year_4.csv` (Dataverse file id `13685110`)
- Direct download: `https://dataverse.harvard.edu/api/access/datafile/13685110?format=original`

## Coverage & schema

- Years **1995–2024** (this project uses **2000–2024**); 232 reporting economies; 1,243 HS4 products.
- Columns used here: `country_iso3_code`, `product_hs92_code`, `year`, `export_value`, `pci`.
  (The file also carries `import_value`, `global_market_share`, `export_rca`, `distance`, `cog`.)
- `pci` (Product Complexity Index) is a **product × year** attribute — identical across all
  countries for a given product-year, which we exploit when aggregating to product level.

## Important caveats

- **PCI is standardized within each year's cross-section.** Absolute PCI levels are not strictly
  comparable across years; a value-weighted *shift* toward higher PCI is interpretable, an absolute
  level change is not. See `docs/analysis.md` §3.
- This vintage re-estimates PCI and rescales `cog` relative to older Atlas releases, so values
  differ slightly from the legacy notebook in `legacy/`.
- The data is already harmonized so that, per product-year, country export values sum to world
  exports of that product (Bustos–Yildirim cleaning). See `docs/analysis.md` §2.
