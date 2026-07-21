# Exports

Committed chart outputs, organized by estimation type. All supply-chain charts
regenerate from `scripts/export_supply_chain_sankey.py`; China+Hong Kong merged
as CHK throughout (see docs/data.md).

- `hubs_nnf/` — per-stage four-column hub charts on the **nonnegativity-identified
  basis** (the canonical set; referenced by the narrative)
- `hubs_varimax/` — varimax-basis variants (≈ identical, |cos| ≥ 0.99)
- `hubs_spectral/` — unrotated spectral-basis variants (hub 1 = the HITS pair,
  descending eigenvalue order)
- `overviews/` — 8-stage chain overviews (dollar/normalized × fine/coarse)
- `network/` — country-node network graph
- `pci/` — PCI-workstream exports (older)
