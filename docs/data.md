# Data: sources, taxonomy, licensing

What the dashboard's numbers rest on: the Atlas files it is built from, the HS6
product baskets behind the **Tech & AI** tab, and the terms each source comes
under. Download steps and schema for the core file are in
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
| `hs12_country_product_year_6.csv` | HS2012 (`doi:10.7910/DVN/YAVJDF`) | country × HS6 × year, 2012 on | Tech & AI tab | `--hs12` |
| `hs12_country_country_product_year_6_*.csv` (2 year ranges) | HS2012 | origin × destination × HS6 × year, 2012–2024 | Tech & AI Corridors view | `--hs12-bilateral all` |

**Why two vintages.** The PCI work uses HS92 because that is where the Atlas
publishes PCI and the longest history. The Tech & AI tab has to use HS2012:
semiconductor codes diverge between the two (integrated circuits are
8542.31/32/33/39 in HS2012 but 8542.11/19 in HS92), and the baskets below are
defined in recent HS revisions.

## 2. Tech & AI basket taxonomy

The Tech & AI tab tracks two external HS6 definitions, both implemented in
`src/gec/classifications.py`:

- **AI compute (Fed)**: the Federal Reserve's deliberately narrow three-code
  basket from the FEDS Note "The Global Trade Effects of the AI Infrastructure
  Boom" (2026): 847150 (AI servers, e.g. NVIDIA DGX), 847180 (other
  data-processing units, e.g. HGX baseboards), 847330 (parts of 8471 machines,
  e.g. GPU / accelerator cards).
- **Semiconductor value chain (OECD)**: OECD (2025), "Mapping the semiconductor
  value chain" (HS 2017), 59 HS6 codes in six groups:

| OECD group | codes |
|---|---|
| Chips | 16 |
| Photosensitive devices | 2 |
| Raw materials | 15 |
| Manufacturing equipment | 14 |
| Foundry inputs | 8 |
| Wafer inputs | 4 |

The tab's baskets (built by `scripts/export_tech_data.py`) are **All**
(semiconductors + AI; the two definitions are disjoint, so nothing is counted
twice), **AI compute**, and each of the six OECD groups.

Caveats that come with HS6 baskets:
- **Within-code heterogeneity.** A data-center GPU module and a commodity part can
  share 847330, so values move with composition as well as with AI demand.
- **Dual use.** The further a code is from the compute silicon, the more non-AI
  trade it carries. Separating it needs national 8–10-digit tariff lines or firm
  data; HS6 cannot.

## 3. Licensing and storage

- The **Atlas** data is free and public (Harvard Dataverse). `data/raw/` and
  `data/derived/` are git-ignored; everything there can be re-downloaded or
  rebuilt with the scripts.
- **Committed**: the dashboard's JSON in `dashboard/public/data/`, results,
  figures, and this documentation.
- The two basket definitions are cited to their sources above; only the HS code
  lists are reproduced here.
