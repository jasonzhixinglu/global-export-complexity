# Global Trade Complexity

Two related workstreams share this repo and its data infrastructure:

1. **PCI / complexity** (the original project, and the dashboard): non-parametric analysis of global
   trade — exports and imports — by **product complexity (PCI)**, built on the Harvard Growth Lab
   *Atlas of Economic Complexity*. Documented in [`docs/pci-analysis.md`](docs/pci-analysis.md).
2. **The AI semiconductor supply chain** (active research): a monthly bilateral panel, time-varying
   matrix factor models, and network measures for the AI-era trade network. Reading order:
   [`docs/research-proposal.md`](docs/research-proposal.md) (the program: claims, model sketch,
   measures, rough answers) → [`docs/supply-chain-narrative.md`](docs/supply-chain-narrative.md)
   (the empirical story 2021–26, with the flow charts) → [`docs/data.md`](docs/data.md) (sources,
   taxonomy, panel construction) → [`docs/modeling-brainstorm.md`](docs/modeling-brainstorm.md)
   (methodology decisions and interpretation, incl. hubs-as-varieties) →
   [`docs/notes/`](docs/notes/) (working notes: computed measure results, proposal sketch).
   Estimation outputs live in [`results/mfm/`](results/mfm/); reference papers in
   [`docs/references/`](docs/references/).

### → Live dashboard: **https://jasonzhixinglu.github.io/global-export-complexity/**

The dashboard answers: *how is a country's trade distributed across the complexity spectrum, who
dominates which complexity bands, and how is that shifting over 2000–2024?* An **Exports / Imports**
toggle flips every view between the two flows.

---

## Dashboard

A static React + Vite + Recharts app (in [`dashboard/`](dashboard/)), deployed to GitHub Pages. It
reads only small precomputed JSON — the heavy data stays in the pipeline. An **Exports / Imports**
toggle drives the country views; the tabs are:

- **Explorer** — for any set of countries (top 50) — individually or aggregated into **region blocs**
  (the per-region "bloc" toggle) — their **market share** or **value** distribution across PCI
  (stacked or lines, 3 smoothness levels), animated over years. Click the chart or drag the PCI
  slider to drill into the **largest products** (export or import) near that complexity.
- **Corridors** — bilateral **origin → destination** flows (top 50 + a Rest-of-world bloc). Pick an
  exporter (or flip to "Imports to" for an importer) and compare its corridors as **partner share**,
  **value ($B)**, or **distribution** across PCI — counterparties individually or grouped into
  **region blocs**. The drill-down lists the anchor country's own top categories near the clicked PCI.
- **Tech & AI** — **AI-compute hardware** (Fed definition) and the **semiconductor value chain**
  (OECD), by country and year, as world share / value / share of the country's own trade — exports
  or imports (e.g. who *ships* chips vs who *buys* them). A **Corridors** sub-view shows the
  bilateral *trade network* for the same HS6 baskets (HS2012 bilateral, 2012–2024): where an
  exporter's chips / AI hardware go, by partner country, over time.
- **About** — top-N coverage by complexity (top exporters or importers), plus methodology, caveats,
  and references.

The Corridors tab is gated behind an `ENABLE_CORRIDORS` flag in `dashboard/src/App.jsx`
(set it to `false` to revert to the three country/sector tabs).

## Methodology (one paragraph)

Two estimands, each with an exact accounting property:

1. **Market share as a function of complexity** — a value-weighted **local-linear** kernel
   regression of each country's product-level share on PCI. Local-linear (over Nadaraya–Watson) has
   lower boundary bias and *reproduces constants*, so shares across all countries sum to **100% by
   construction**.
2. **Distribution of trade value across complexity** — a value-weighted **kernel density** over
   PCI; total mass is conserved exactly, with only mean-zero redistribution. For the dashboard
   each country-year distribution is stored as a small **Gaussian mixture** (K chosen per country
   by fidelity to the raw data, K≈2–8) and reconstructed in the browser — smoothness becomes a
   render-time blur (`σ → √(σ²+b²)`), shrinking that payload ~36× while staying smooth. The mixture
   is faithful in *location* (median KS 6.1%, beating the KDE it replaced; transport error W1 ≈ 0.03
   PCI); it only smooths over sharp single-product spikes — see [`docs/pci-analysis.md`](docs/pci-analysis.md) §3.3.

Both estimands run on either flow (the same estimators applied to `import_value`), exposed via the
Exports / Imports toggle.

Full write-up — including how to reconcile non-parametric smoothing with trade-accounting
identities — in [`docs/pci-analysis.md`](docs/pci-analysis.md).

## Data

- **Atlas of Economic Complexity** (Harvard Growth Lab), HS92 HS4 `country × product × year`,
  2000–2024 — the core dataset. Tech/AI uses the **HS2012** vintage (codes like 8486/8542 don't
  exist in HS92). Provenance in [`data/README.md`](data/README.md).
- **Atlas bilateral** (HS92 HS6 `origin × destination × product × year`) — reconciled flows for the
  **Corridors** tab; aggregated to HS4, top 50 + ROW. Imports are the same matrix read by destination.
- **Tech & AI baskets** — AI compute from the Fed FEDS Note (2026); semiconductor value chain from
  OECD (2025). See [`docs/data.md`](docs/data.md) (basket tiers, national
  monthly sources, and the Haver cross-check).
- **UN Comtrade** — optional puller for more recent years (raw, mirror-reconstructable for late
  filers); see [`docs/data.md`](docs/data.md).

## Repository layout

```
src/gec/               importable package
  config.py            paths + constants (YEARS, N_TOP, bandwidths, dataset IDs)
  data.py              load / clean / rank exporters / product & bilateral aggregation
  estimators.py        local-linear shares, KDE, mass-conserving bins, calibration
  classifications.py   AI / semiconductor HS code sets (Fed, OECD)
  comtrade.py          UN Comtrade pulls (direct + mirror) + availability checks
  plotting.py          headless matplotlib helpers
scripts/               two workstreams -- see scripts/README.md for the full index
  PCI pipeline:        download_data -> compute_surfaces -> make_figures -> run_diagnostics
  dashboard exports:   export_dashboard_data, export_gmm_*, export_tech_*, ...
  supply-chain data:   fetch_comtrade_monthly, fetch_tdm, build_monthly_panel
  estimation:          prototype_mfm (annual), tvmfm_monthly_anchored (time-varying)
  charts:              export_supply_chain_sankey
dashboard/             React/Vite/Recharts app (deployed to GitHub Pages)
docs/                  data.md (master data reference) · research-proposal.md ·
                       supply-chain-narrative.md · modeling-brainstorm.md ·
                       pci-analysis.md · notes/ · references/ · tdm/
results/               figures & tables (PCI) · mfm/ (factor models) · panel_monthly/
exports/               committed charts (supply-chain set + PCI-era)
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
python scripts/export_gmm_data.py           # distribution curves as Gaussian mixtures (gmm.json)
python scripts/export_pci_products.py
python scripts/export_country_products.py   # per-country top categories (corridor drill-down)
python scripts/export_tech_data.py          # needs the HS12 file: python scripts/download_data.py --hs12
python scripts/export_tech_bilateral.py     # needs HS2012 bilateral: python scripts/download_data.py --hs12-bilateral all
cd dashboard && npm install && npm run dev    # local; `npm run build` for production
```

Tune the analysis in [`src/gec/config.py`](src/gec/config.py) (`N_TOP`, `BANDWIDTH`, `YEARS`,
`COVER_THRESHOLDS`). Pushing changes under `dashboard/**` auto-deploys via
[`.github/workflows/deploy.yml`](.github/workflows/deploy.yml).

## Headline findings

- Estimators respect the accounting exactly: shares sum to 100% to machine precision; the dollar
  distribution conserves total exports with only mean-zero redistribution.
- The **top-20 exporters cover ~72%** of world trade on average but only ~45–50% at low complexity
  (commodities are fragmented across many economies); **top-50 reaches ~93%** (imports analogous,
  ranked by top importers).
- China's export distribution marches up and right across the complexity spectrum over 2000–2024;
  in AI compute and chips a handful of East-Asian economies dominate exports, while imports of those
  same chips concentrate heavily in China — visible by flipping the Exports / Imports toggle.
