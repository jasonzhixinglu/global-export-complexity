# Data: sources and licensing

What the dashboard's numbers rest on: the Atlas files it is built from and the
terms each source comes under. Download steps and schema for the core file are in
[data/README.md](../data/README.md); the PCI methodology is in
[pci-analysis.md](pci-analysis.md).

---

## 1. Sources: the Atlas of Economic Complexity

Everything in the dashboard comes from the Harvard Growth Lab's **Atlas of
Economic Complexity**, downloaded from Harvard Dataverse. The Atlas is
*reconciled*: exporter and importer reports are mirrored and reliability-weighted
(Bustos–Yildirim), so for each product-year the country values sum to world
trade. It carries the Product Complexity Index (PCI), is annual, and lags about
1.5 years. Dataverse file IDs live in `src/gec/config.py`.

| file(s) | vintage | level | used for | download |
|---|---|---|---|---|
| `hs92_country_product_year_4.csv` | HS92 (`doi:10.7910/DVN/T4CHWJ`) | country × HS4 × year, with PCI | Explorer and About tabs; the PCI analysis | `python scripts/download_data.py` |
| `hs92_country_country_product_year_6_*.csv` (4 year ranges) | HS92 | origin × destination × HS6 × year | Corridors tab (aggregated to HS4) | `--bilateral all` |

## 2. Licensing and storage

- The **Atlas** data is free and public (Harvard Dataverse). `data/raw/` and
  `data/derived/` are git-ignored; everything there can be re-downloaded or
  rebuilt with the scripts.
- **Committed**: the dashboard's JSON in `dashboard/public/data/`, results,
  figures, and this documentation.
