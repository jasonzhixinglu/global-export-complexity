# Global Export Complexity

Non-parametric analysis of global exports by **product complexity (PCI)** — across country, time,
and now technology/AI — built on the Harvard Growth Lab *Atlas of Economic Complexity*, with an
interactive dashboard.

### → Live dashboard: **https://jasonzhixinglu.github.io/global-export-complexity/**

The dashboard answers: *how is a country's export activity distributed across the complexity
spectrum, who dominates which complexity bands, and how is that shifting over 2000–2024?*

---

## Dashboard

A static React + Vite + Recharts app (in [`dashboard/`](dashboard/)), deployed to GitHub Pages. It
reads only small precomputed JSON — the heavy data stays in the pipeline. Three tabs:

- **Explorer** — for any set of countries (top 50 exporters), their **market share** or **export
  value** distribution across PCI (stacked or lines), animated over years. Click the chart or drag
  the PCI slider to drill into the **largest products** near that complexity.
- **Tech & AI** — exports of **AI-compute hardware** (Fed definition) and the **semiconductor value
  chain** (OECD), by country and year, as world share / export value / share of the country's own
  exports.
- **About** — top-N coverage by complexity, plus methodology, caveats, and references.

## Methodology (one paragraph)

Two estimands, each with an exact accounting property:

1. **Market share as a function of complexity** — a value-weighted **local-linear** kernel
   regression of each country's product-level share on PCI. Local-linear (over Nadaraya–Watson) has
   lower boundary bias and *reproduces constants*, so shares across all countries sum to **100% by
   construction**.
2. **Distribution of export value across complexity** — a value-weighted **kernel density** over
   PCI; total mass is conserved exactly, with only mean-zero redistribution.

Full write-up — including how to reconcile non-parametric smoothing with trade-accounting
identities — in [`docs/analysis.md`](docs/analysis.md).

## Data

- **Atlas of Economic Complexity** (Harvard Growth Lab), HS92 HS4 `country × product × year`,
  2000–2024 — the core dataset. Tech/AI uses the **HS2012** vintage (codes like 8486/8542 don't
  exist in HS92). Provenance in [`data/README.md`](data/README.md).
- **Tech & AI baskets** — AI compute from the Fed FEDS Note (2026); semiconductor value chain from
  OECD (2025). See [`docs/ai-semiconductor-classification.md`](docs/ai-semiconductor-classification.md).
- **UN Comtrade** — optional puller for more recent years (raw, mirror-reconstructable for late
  filers); see [`docs/comtrade.md`](docs/comtrade.md).

## Repository layout

```
src/gec/               importable package
  config.py            paths + constants (YEARS, N_TOP, bandwidths, dataset IDs)
  data.py              load / clean / rank exporters / product & bilateral aggregation
  estimators.py        local-linear shares, KDE, mass-conserving bins, calibration
  classifications.py   AI / semiconductor HS code sets (Fed, OECD)
  comtrade.py          UN Comtrade pulls (direct + mirror) + availability checks
  plotting.py          headless matplotlib helpers
scripts/
  download_data.py        fetch raw CSVs from Harvard Dataverse (HS4, bilateral)
  compute_surfaces.py     kernel surfaces (share / density / coverage) -> data/derived/
  make_figures.py         static analysis figures -> results/figures/
  run_diagnostics.py      conservation & adding-up checks -> results/tables/
  run_all.py              download -> compute -> figures -> diagnostics
  export_dashboard_data.py  surfaces -> dashboard/public/data (meta, series, coverage, anchors)
  export_tech_data.py       HS12 -> AI/semiconductor basket JSON (techai.json)
  export_pci_products.py    per-PCI product drill-down JSON (pci_products.json)
  fetch_comtrade.py         pull recent-year HS4 exports from UN Comtrade
  explore_bilateral_pci.py  prototype: origin x destination complexity (sizing)
dashboard/             React/Vite/Recharts app (deployed to GitHub Pages)
docs/                  analysis.md · comtrade.md · ai-semiconductor-classification.md
results/               committed figures & tables
data/                  git-ignored raw + derived (download / regenerate)
legacy/                original exploratory notebook (superseded)
```

## Reproduce

```bash
pip install -r requirements.txt

# analysis pipeline (downloads ~430 MB on first run)
python scripts/run_all.py

# regenerate the dashboard's data, then build the site
python scripts/export_dashboard_data.py
python scripts/export_pci_products.py
python scripts/export_tech_data.py          # needs the HS12 file (download_data --hs12*)
cd dashboard && npm install && npm run dev    # local; `npm run build` for production
```

Tune the analysis in [`src/gec/config.py`](src/gec/config.py) (`N_TOP`, `BANDWIDTH`, `YEARS`,
`COVER_THRESHOLDS`). Pushing changes under `dashboard/**` auto-deploys via
[`.github/workflows/deploy.yml`](.github/workflows/deploy.yml).

## Headline findings

- Estimators respect the accounting exactly: shares sum to 100% to machine precision; the dollar
  distribution conserves total exports with only mean-zero redistribution.
- The **top-20 exporters cover ~72%** of world trade on average but only ~45–50% at low complexity
  (commodities are fragmented across many economies); **top-50 reaches ~93%**.
- China's export distribution marches up and right across the complexity spectrum over 2000–2024;
  in AI compute and chips, a handful of East-Asian economies dominate.
