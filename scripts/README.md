# Scripts index

Data sources and downloads in [docs/data.md](../docs/data.md); methodology in
[docs/pci-analysis.md](../docs/pci-analysis.md).

## PCI workstream and dashboard


- pipeline: `download_data.py` → `compute_surfaces.py` → `make_figures.py` →
  `run_diagnostics.py` (`run_all.py` chains them)
- dashboard exports: `export_dashboard_data.py`, `export_gmm_data.py`,
  `export_gmm_bilateral.py`, `export_pci_products.py`, `export_country_products.py`,
  `export_share_chart.py`, `export_tech_data.py`, `export_tech_bilateral.py`
- validation/prototypes: `validate_bilateral.py`, `plot_gmm_check.py`,
  `explore_bilateral_pci.py`, `prototype_bilateral_*.py`, `prototype_gmm_*.py`,
  `prototype_compress.py`, `prototype_share_ratio.py`, `prototype_truth.py`
- `cdp.mjs` — dashboard screenshot helper
