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

## Chart packs

- `chart_pack.tex` — **editable source** of the desktop pack: titles and
  captions are plain LaTeX text, one `\chartpage{title}{caption}{figure}`
  per page. Compile with `cd exports && pdflatex chart_pack.tex`, or
  `python scripts/build_chart_pack_tex.py --compile`.
- `chart_pack.pdf` — compiled from the .tex.
- `chart_pack_mobile.pdf` — phone layout, built by
  `python scripts/build_chart_pack.py mobile`.
- Figures come from their generator scripts; rerun a generator to refresh a
  chart, then recompile. Charts embed as vector PDFs, so zoom stays sharp.
