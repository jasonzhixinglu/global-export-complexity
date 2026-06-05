# Extending to recent years with UN Comtrade

The Atlas (reconciled, with PCI) lags ~1.5 years. UN Comtrade is more current, so this repo
includes a puller (`scripts/fetch_comtrade.py`, `src/gec/comtrade.py`) to pull HS4 export data and
map it onto the Atlas schema. This note records what is and isn't feasible — established by probing
the live API — so the limits are explicit.

## What Comtrade can and cannot give us (probed June 2026)

| question | finding |
|---|---|
| Is 2025 available? | **Partially.** Early filers have annual 2025 (USA, Germany, Korea …). |
| China 2025? | **Not filed directly.** China's latest *direct* annual is **2024**. |
| Can we still get China 2025? | **Yes, by mirror** — 66+ partners already report 2025 imports *from* China; for HS 8517 they sum to ~$208B CIF, within ~3% of China's own 2024 figure. |
| Is it reconciled? | **No.** Raw reporter declarations: no CIF/FOB removal, no mirror reconciliation, no reliability weighting, no imputation. That is the Atlas/BACI value-add (see `docs/analysis.md` §2). |
| Does it have PCI? | **No.** We join the Atlas PCI as a proxy (default 2024). |
| HS revision? | Recent years serve only **as-reported** (`clCode='HS'`, ≈HS2022); `H0`/HS92 is empty for 2024–25. We map as-reported HS4 → Atlas HS92 by identity, which covers **~97–98% of export value** at the 4-digit level. |

## Two pull modes

- **direct** — a country's own exports to World (flow `X`, FOB). Used when the country filed.
- **mirror** — sum of all partners' imports *from* the country (flow `M`, CIF, deflated by a flat
  `CIF_FOB=1.10`). Used as a fallback for late filers like China. **Requires a key** in practice:
  the all-reporter pull far exceeds the free preview's 500-row cap.

`--mode auto` (default) tries direct, then falls back to mirror per country.

## API key

The **free** tier is sufficient — premium (bulk) is not needed. Register a B2C account at
<https://comtradedeveloper.un.org/>, subscribe to the **free** product under */products* (auto-
approved), and copy the subscription key. Free limits: **100k records/call, 500 calls/day**.

Our pulls fit comfortably: direct ≈1.2k rows/country, mirror ≈60–70k rows (one call). A full
world-denominator pull (~240k rows) exceeds 100k/call and must be chunked into ~3 calls (still
free). Premium (shop.un.org/comtrade) is only for million-row bulk files.

## Usage

```bash
# free key from https://comtradedeveloper.un.org/  -> /products -> free
$env:COMTRADE_API_KEY="..."                        # bash: export COMTRADE_API_KEY=...
python scripts/fetch_comtrade.py --year 2025 --reporters top30
python scripts/fetch_comtrade.py --year 2024 --reporters CHN,USA,DEU --mode auto
```

Output: `data/raw/comtrade_hs4_<year>.csv` (Atlas-like schema + a `provenance` column marking
`direct` vs `mirror(n=partners)`), plus a `.report.json` with per-country HS92 match coverage.

Without a key the script uses the free preview endpoint (≤500 rows/call) — fine for a smoke test
(direct mode), but values are **truncated** and mirror is unusable. Set a key for real pulls.

## Caveats — read before using these numbers

- **Provisional shares for incomplete years.** Market share = country / world. For 2025 the *world*
  denominator is missing late filers (incl. China's direct exports), so any 2025 share is
  provisional until coverage fills in. The puller flags provenance so you can see which countries are
  mirror-based.
- **Raw, not reconciled.** A big reporter's own FOB exports are reliable; small/irregular reporters
  and the world total are not, the way the Atlas's reconciled figures are.
- **PCI is a proxy.** We attach Atlas-2024 PCI to recent-year codes. Defensible (PCI is standardized
  and slow-moving) but not a re-estimated 2025 PCI.
- **HS concordance is identity-based.** ~2–3% of value sits in HS4 headings that changed between the
  as-reported revision and HS92; those are currently unmatched (no PCI) rather than concorded. A
  formal HS2022→HS1992 4-digit concordance is the future refinement.

## Recommended use

1. **Validation:** pull a *complete* past year (e.g. 2024, where everyone incl. China filed) and
   compare to the Atlas to characterise the raw-vs-reconciled gap.
2. **Early-warning 2025:** direct for filers + mirror for China, clearly labelled provisional.
3. **Production 2025:** prefer the next **Atlas vintage** (reconciled + native PCI) when released —
   the main pipeline ingests it by changing `DATAVERSE_FILE_ID` in `src/gec/config.py`.
