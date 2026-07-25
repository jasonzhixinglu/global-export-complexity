# The monthly bilateral panel: construction and validation

How `data/derived/panel_semi_monthly.parquet` is built from UN Comtrade and
Trade Data Monitor, and how closely it replicates the Harvard Atlas. This is
the reference for anyone (including future us) asking "where does a number in
the panel come from and how much should I trust it?"

**Scope.** 60 HS6 codes (the Fed AI-compute trio + the OECD semiconductor
value-chain list, stages 1–8; `src/gec/classifications.py`), 30 countries +
rest-of-world (ROW), monthly, 2017-01 to the balanced endpoint (currently
2026-04). One reconciled dollar value per exporter x importer x code x month,
with both underlying reports and a provenance tag preserved per cell.

The 2017 start matches the HS2017 vintage of the code list (avoiding HS2012
concordance work) and puts the 2018–19 tariff war in sample.

---

## 1. Sources and what each contributes

| source | role | files |
|---|---|---|
| UN Comtrade monthly | backbone: all reporters x all partners, both flows | `data/raw/comtrade_monthly/` (committed; public data) |
| TDM | the three holes Comtrade cannot fill: **Taiwan** (never in Comtrade; TDM has primary customs data), **China** after 2024-12, **Vietnam** via the VN2 preliminary edition (confirmed back to 2017) | `data/raw/tdm/` (git-ignored; licensed) |
| UN Comtrade annual, all-product totals | the aggregate level at which the Growth Lab estimates freight ratios and reliability scores (their Steps 2–3); carries the dual-basis `cifvalue`/`fobvalue` fields | `data/raw/comtrade_totals/` |
| CEPII GeoDist | distance and contiguity for the freight regression | `data/raw/dist_cepii.xls` |

Fetch scripts: `fetch_comtrade_monthly.py` (density-sized batches, recursive
split on the 100k row cap, quota-aware waits), `fetch_tdm.py`,
`fetch_comtrade_totals.py`. All are cached per batch; re-running only fetches
what is missing.

## 2. Construction pipeline (`scripts/build_monthly_panel.py`)

1. **Load and standardize.** Comtrade M49 codes map to ISO3 via the Comtrade
   partner reference (490 = Taiwan); TDM TSVs parse to the same schema. Every
   record is one reporter's view of one flow: (reporter, partner, code, month,
   flow, value, source).
2. **Deduplicate at the original partner level.** Where Comtrade and TDM both
   carry the same report, Comtrade wins. Order matters: dedupe happens BEFORE
   partners are collapsed, then non-kept partners sum into ROW. (The audit
   found the original code deduped after collapsing — which kept one arbitrary
   partner's value per ROW cell and silently dropped the rest. Fixed and
   verified: the test cell lost 100% of its ROW value before the fix.)
3. **Reconcile the two views of each flow — the Growth Lab pipeline** (Bustos,
   Yildirim et al., GL WP 251 / Scientific Data 2026), implemented at the
   levels they specify:
   - *Step 2, CIF→FOB:* regression ln(CIF/FOB) on log distance, contiguity,
     exporter FE, importer FE — fit per year on the importer reports that carry
     BOTH bases in the all-product totals (~4–5k obs/year, ~36 reporting
     countries), with sample hygiene (ratios outside [0.9, 3.0] and flows under
     $100k dropped) and FE centring so countries outside the estimation sample
     get the average effect, not an arbitrary zero. Predictions capped at 1.20
     (their cap; 0% of ours bind it, median ratio 1.07).
   - *Step 3, reliability:* pair discrepancy D = |X − M_fob| / (X + M_fob),
     D = 1 for single-sided pairs, regressed on country dummies over the full
     ~244-country trade network per year; negative coefficients clipped to
     zero; base country chosen by R²; reliability = 1 − α.
   - *Step 4, pair weights:* softmax over the two reliabilities; reporters in
     the bottom decile are disregarded in favour of the reliable partner;
     single-sided flows taken at full weight.
   - *Step 5, product level (the step that matters most):* the weights
     reconcile **pair-year totals only**. Code-month cells carry the
     **exporter's reported composition**, rescaled by the pair-year factor
     (reconciled total / exporter-reported total); the importer side is used
     only where the exporter is silent (77% of cells ride on the exporter
     side). This mirrors Atlas's own allocation: their published value is a
     single reconciled number per flow that tracks the exporter report at HS6
     level — importer product-level classification noise is what their "XXXX"
     residual code absorbs, so it must not be blended into code cells.
4. **Balanced endpoint.** The panel ends at the last month every kept country
   has reported (any side, any source), excluding a designated mirror-fallback
   set (currently FRA, PHL, IND, ITA, ESP, SWE) whose corridors survive via
   partner reports; only fallback-fallback and fallback-ROW cells go dark
   (~0.06% of monthly value; quantified in the build report's lag analysis).

Deliberate deviations from the published Atlas pipeline, all documented in the
script docstring: no ANS subtraction (our unknown-partner trade lands in ROW,
which cannot double-count), no XXXX residual code (requires all-product
coverage per pair), no LT vintage harmonisation (codes as reported — measured
consequence below), ROW is an aggregate rather than a reporter.

## 3. Validation against Atlas

Design: aggregate the panel to annual, match Atlas HS12 bilateral cells
(exporter x importer x code x year, kept-kept corridors, both values > $0.1M,
2017–2024; ~164k cells ≈ 92% of Atlas cells for these codes). Both log-based
statistics (every corridor equal) and value-weighted level statistics (logs
overstate small linkages) are reported — the standing per-code table is in
`results/panel_monthly/build_report.md`.

Headline, full sample:

| statistic | value |
|---|---|
| log-correlation | 0.977 |
| median corridor ratio (panel/Atlas) | 1.10 |
| IQR of log ratio (middle half of cells) | 0.21 (~0.99x–1.22x) |
| value-weighted share within ±25% | 79% |
| value-weighted MAPE | 22% |
| aggregate ratio | 1.16 (1.11 on the CHK basis) |

Uniform across years (IQR 0.20–0.23 in each of 2017–2024, medians 1.09–1.12);
55/60 codes have IQR < 0.30; cells where both sides report all year — the
majority of value — sit at IQR 0.15.

Single-source checks that anchored the pipeline along the way:

- Comtrade world totals per code-year vs Atlas: ratio 1.05 overall (compute
  codes 0.95–1.06) once partner-World aggregate rows are excluded.
- TDM Taiwan vs Atlas Taiwan: 1.017 overall, median exactly 1.00 — our Taiwan
  rests on primary customs data where Atlas's is mirror-constructed.

**How the discrepancy causes were established** (full record:
`results/panel_monthly/atlas_discrepancy_audit.md`): hypothesised causes were
tested as falsifiable predictions, not asserted. The first attribution
(HS-vintage reallocation) was *rejected* by a variance decomposition; the
surviving clue — disagreement concentrated where two conflicting reports must
be blended — was confirmed by single-code, single-year pilots that proved (a)
Atlas publishes one reconciled value per flow (both perspectives identical to
<0.1% in 100% of tested corridors) and (b) that value tracks the exporter
report at HS6 level (IQR ~0.13). Implementing Step 5 accordingly collapsed the
cell-level IQR from 0.55 to 0.21. Protocol note: every such test runs on one
code and a sub-window first, then scales.

## 4. Known residual differences and what they mean for analysis

1. **A fairly uniform level offset (~+10% median, +11% aggregate on the CHK
   basis).** Consistent with Atlas's XXXX step draining discrepant value out of
   real codes, entrepot netting, and annual-file revisions. A near-uniform
   scalar cancels in shares and compositions — which is what the factor model
   consumes.
2. **Mixed-coverage cells are the widest cut (IQR 0.35).** Months where a
   corridor flips between both-sided and single-sided make monthly and annual
   reconciliation genuinely differ. Second-order; shrinks as laggards file.
3. **Dual-use equipment codes (8486xx, 903141, 901210) are the loosest codes
   (IQR up to 0.36).** Single-code claims there carry more uncertainty.
4. **Codes are as-reported (no LT harmonisation).** Within-8542 sibling codes
   show offsetting disagreement with Atlas; results hanging on a *single* 8542
   subheading inherit that uncertainty, while basket- and stage-level results
   do not.

Guidance: run analyses at basket/stage level on the CHK basis (the measured
agreement is tightest there); cite the audit when a claim rests on one HS6
code in isolation.

## 5. Regeneration

```
python scripts/fetch_comtrade_monthly.py semi   # + compute; batch caches, quota-aware
python scripts/fetch_tdm.py semi                # licensed extracts, local only
python scripts/fetch_comtrade_totals.py         # annual all-product totals (Steps 2-3)
python scripts/build_monthly_panel.py           # panel + build_report.md
python scripts/audit_atlas_discrepancy.py       # discrepancy attribution (optional)
```

The legacy 3-code panel (`panel_ai_compute_monthly.parquet`, 2020+, pre-audit
methodology) remains on disk so existing results stay reproducible; **all new
work should read `panel_semi_monthly.parquet`**. Existing TV-MFM results
predate this panel and are queued for re-estimation on it.
