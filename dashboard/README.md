# Global Export Complexity — dashboard

Static React + Vite + Tailwind + Recharts dashboard for exploring exports across the Product
Complexity Index (PCI), deployed to GitHub Pages. Templated on the nsicx-dashboard.

## Tabs
- **Explorer** — 3-panel: left = year + country picker (top 50 exporters, searchable); middle =
  market-share / export-value / distribution across PCI (stacked or lines, animatable); right =
  the largest products near a clicked/dragged PCI.
- **Tech & AI** — AI-compute and semiconductor value-chain baskets by country and year (world
  share / export value / share of own exports), from HS2012 data.
- **About** — top-N coverage by complexity + an accordion of methodology, caveats, and references.

## Data
The dashboard reads precomputed static JSON in `public/data/` (`meta`, `series`, `coverage`,
`anchors`, `techai`, `pci_products`), generated from the project pipeline:

```bash
python scripts/export_dashboard_data.py    # meta/series/coverage/anchors (after compute_surfaces.py)
python scripts/export_pci_products.py      # per-PCI product drill-down
python scripts/export_tech_data.py         # AI/semiconductor baskets (HS2012)
```

Regenerate whenever the surfaces or classifications change, then commit the updated JSON.

## Develop / build
```bash
cd dashboard
npm install
npm run dev        # local dev server
npm run build      # production build -> dist/
```

## Deploy
Pushing changes under `dashboard/**` to `main` triggers `.github/workflows/deploy.yml`, which builds
and publishes to GitHub Pages. **One-time setup:** in the repo Settings → Pages, set *Source* to
**GitHub Actions**. The site is served at `/<repo>/` (base path set in `vite.config.js`).
