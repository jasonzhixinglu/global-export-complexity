# Global Export Complexity — dashboard

Static React + Vite + Tailwind + Recharts dashboard for exploring exports across the Product
Complexity Index (PCI), deployed to GitHub Pages. Templated on the nsicx-dashboard.

## Views
- **Explorer** — distribution across PCI for any set of countries; toggle market share / export
  value / normalized distribution; lines or stacked; animate across 2000–2024.
- **Segment** — pick a complexity band (low/mid/high), rank countries within it, and watch the
  leaders evolve over time.
- **Country** — single-country deep dive: profile across PCI, total exports and value-weighted
  average complexity over time.
- **Coverage · About** — top-N world-export coverage by complexity, plus methodology.

## Data
The dashboard reads precomputed static JSON in `public/data/` (`meta`, `series`, `coverage`,
`anchors`), generated from the project pipeline by:

```bash
python scripts/export_dashboard_data.py    # run from the repo root, after compute_surfaces.py
```

Regenerate that whenever the surfaces change, then commit the updated JSON.

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
