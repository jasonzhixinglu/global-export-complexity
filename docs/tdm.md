# Trade Data Monitor (TDM) — monthly AI-compute pulls

TDM (tradedatamonitor.com, personal login) supplements UN Comtrade for the
monthly bilateral AI-compute panel (HS **847150 / 847180 / 847330**). It sources national
customs directly (~1-month lag), covering what Comtrade lacks or lags on:

| gap | Comtrade status (checked 2026-07) | TDM fills |
|---|---|---|
| Taiwan | never reports (mirror-only, partner code 490) | full direct X+M history, through 2026-06 |
| China | monthly ends **2024-12** | 2025-01 onward, through 2026-05 |
| Vietnam | monthly ends **2023-12** | edition **"Vietnam (preliminary) 2"**, API code `VN2`: full X+M history 2020-01 through 2026-04 |
| THA / KOR / SGP / FRA / TUR | end 2025-02 / 2025-12 (×4) | recent top-ups |

Caution: [tdm/tdm-api-specification.xlsx](tdm/tdm-api-specification.xlsx) is **outdated**
— its 163-entry reporter list omits the Vietnam (preliminary) editions entirely (plain
`VN`/`VNM`/`VIETNAM` reporter queries return empty). `VN2` was found by probing after
the edition appeared in the query dashboard; treat the dashboard's reporter dropdown,
not the workbook, as the source of truth for available editions. The "(preliminary)"
label suggests provisional figures — compare the 2020-2023 overlap against Comtrade's
final Vietnam data to gauge revision size.

## API (preferred): scripted pulls

The "Special Report - Download" form's **Generate API URL** button exposes a plain GET
endpoint (`www1.tdmlogin.com/tdm/api/api.asp`) taking the same parameters (ISO2
`reporter`, `periodBegin/periodEnd` as YYYYMM, `flow` E/I, comma-joined `hsCode`,
`separator=T`, `ISO3=Y`, ...). `scripts/fetch_tdm.py` wraps it and runs the standing
pull set below; credentials live in the git-ignored `.env` (`TDM_USERNAME` /
`TDM_PASSWORD`). Output lands in `data/raw/tdm/tdm_<reporter>_<flow>_<begin>_<end>.tsv`.

Response format: **UTF-16 LE** TSV with columns FLOW, CTY_RPT, RPT_ISO, REPORTER,
CTY_PTN, PTN_ISO, PARTNER, COMMODITY, YEAR, MONTH, VALUE (USD), QTY1/UNIT1,
QTY2/UNIT2, CURRENCY. Quantity units: Taiwan reports SET+KG, China KG+NO (pieces).

```
python scripts/fetch_tdm.py                    # standing set (6 pulls)
python scripts/fetch_tdm.py TW E 202001 202606 # one custom pull
```

## The standing report set (portal fallback)

Vendor documentation lives in [docs/tdm/](tdm/): user guide, quick tips, the
Comtrade/TradeMap comparison sheet, the API specification workbook (reporter/partner/
language code lists — reporter codes are mostly ISO2 with edition variants like USC =
US Consumption, CNC, "(CIF)" editions; partner codes are TDM-internal names like
`VIETNAM`, `AFGHAN`), and the report-by-email help file.

Portal workflow: `Username -> Report -> Download` ("Special Report - Download" form);
see [tdm/tdm-report-by-email-help.pdf](tdm/tdm-report-by-email-help.pdf). Common settings for
every request: **Frequency = Monthly**, **Commodity = 847150, 847180, 847330**,
**Partner countries = All**, **Aggregate Partner Countries = No** (keeps bilateral
detail), "To" period = latest available month. One request at a time; use
"Get Report By Email". Save the parameter set as a **Profile** (and try **Scheduler**)
so the monthly refresh is a re-run, not a re-entry.

| # | Reporting countries | Trade flow | From |
|---|---|---|---|
| A | Taiwan | Exports | 2020-01 |
| B | Taiwan | Imports | 2020-01 |
| C | China | Exports | 2024-01 |
| D | China | Imports | 2024-01 |
| E | Vietnam | Exports | 2024-01 |
| F | Vietnam | Imports | 2024-01 |
| G | Thailand, Korea South, Singapore, France, Turkey | Exports | 2025-01 |
| H | Thailand, Korea South, Singapore, France, Turkey | Imports | 2025-01 |

China/top-up start dates deliberately overlap Comtrade's coverage by a year — the overlap
months validate TDM-vs-Comtrade consistency before the splice.

## Handling the files

- Save email attachments to **`data/raw/tdm/`** (git-ignored). Suggested names:
  `tdm_<reporter(s)>_<X|M>_<fromYYYYMM>.csv` — keep whatever columns TDM emits,
  especially quantity/weight fields.
- **Licensing:** TDM is subscription data. Raw extracts must never be committed or
  pushed; only derived aggregates enter the repo (same discipline as Atlas raw files).
- Ingestion merges TDM with the Comtrade monthly pulls into one provenance-flagged
  panel (per-cell source: direct import report / export mirror / TDM), import-reported
  design, ~30 countries + ROW. See docs/comtrade.md for the Comtrade side.
