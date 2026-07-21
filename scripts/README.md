# Scripts index

Two workstreams share this folder. Regeneration commands and data prerequisites
in [docs/data.md](../docs/data.md).

## Supply-chain workstream (active research)

**Data acquisition & panel**
- `fetch_comtrade_monthly.py` — Comtrade monthly bilateral pulls (backbone)
- `fetch_tdm.py` — TDM API pulls (TWN/CHN/VN2 + top-ups)
- `fetch_comtrade.py` — annual HS4 pulls with PCI proxy (early-warning years)
- `extract_ai_compute.py` — slice the 3 compute codes from the Atlas bilateral file
- `build_monthly_panel.py` — assemble the reconciled balanced monthly panel

**Estimation**
- `prototype_mfm.py` — constant-loading annual MFMs (results/mfm/annual)
- `tvmfm_monthly_anchored.py` — era-anchored time-varying MFMs (the main model)
- `tvmfm_monthly.py` — superseded chained version (kept: produces the archive run)
- `prototype_tvmfm_bandwidth.py` — window-length OOS experiment (chose 12m)
- `prototype_nonneg_rotation.py` — nonnegativity-rotation identification experiment

**Outputs**
- `export_supply_chain_sankey.py` — all supply-chain charts (hub charts, overviews, network)

## PCI workstream (dashboard; see docs/pci-analysis.md)

- pipeline: `download_data.py` → `compute_surfaces.py` → `make_figures.py` →
  `run_diagnostics.py` (`run_all.py` chains them)
- dashboard exports: `export_dashboard_data.py`, `export_gmm_data.py`,
  `export_gmm_bilateral.py`, `export_pci_products.py`, `export_country_products.py`,
  `export_share_chart.py`, `export_tech_data.py`, `export_tech_bilateral.py`
- validation/prototypes: `validate_bilateral.py`, `plot_gmm_check.py`,
  `explore_bilateral_pci.py`, `prototype_bilateral_*.py`, `prototype_gmm_*.py`,
  `prototype_compress.py`, `prototype_share_ratio.py`, `prototype_truth.py`
- `cdp.mjs` — dashboard screenshot helper
