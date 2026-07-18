# Trade Data Monitor (TDM) — monthly AI-compute pulls

TDM (tradedatamonitor.com, personal login, **no API**) supplements UN Comtrade for the
monthly bilateral AI-compute panel (HS **847150 / 847180 / 847330**). It sources national
customs directly (~1-month lag), covering what Comtrade lacks or lags on:

| gap | Comtrade status (checked 2026-07) | TDM fills |
|---|---|---|
| Taiwan | never reports (mirror-only, partner code 490) | full direct X+M history |
| China | monthly ends **2024-12** | 2025-01 onward |
| Vietnam | monthly ends **2023-12** | 2024-01 onward |
| THA / KOR / SGP / FRA / TUR | end 2025-02 / 2025-12 (×4) | recent top-ups |

## The standing report set

Portal workflow: `Username -> Report -> Download` ("Special Report - Download" form);
see [tdm-report-by-email-help.pdf](tdm-report-by-email-help.pdf). Common settings for
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
