# Data: sources, taxonomy, panels — the master reference

Everything the project's numbers rest on, in one place: what products we track
(taxonomy), where the data comes from (sources, with their properties and
trade-offs), what we build from it (panels), how fresh each piece is, and the
operational detail to regenerate any of it. Vendor/API notes, the taxonomy, and
the national-source intelligence formerly spread across `comtrade.md`, `tdm.md`,
and `tech-ai-taxonomy.md` are all folded in here (originals in git history).

---

## 1. The product taxonomy (what we track)

Organizing principle: **proximity to the GPU**, arranged as supply-chain stages.
Codes are HS6; stage definitions follow the OECD semiconductor value-chain
mapping (2025) and the Fed's AI-compute basket (FEDS Note 2026). The closer a
code is to the compute silicon, the more cleanly it is "AI/semiconductor"; the
further out, the more dual-use dilution — the reason for tiering (below).

| stage | codes | 2024 world trade | monthly? |
|---|---|---|---|
| 1 raw materials | 280461 silicon, rare gases 280421/29, Ga/Ge/In 282560/8112xx, chemicals | $13B | **yes** (2017-01+) |
| 2 wafers & inputs | 381800, 3701xx/370790 | $25B | **yes** (2017-01+) |
| 3 litho & optics inputs | 9001xx/9002xx, 901210/90, 903141 | $38B | **yes** (2017-01+) |
| 4 fab equipment | 8486xx, metrology 903082/84/9033, fab plant | $244B | **yes** (2017-01+) |
| 5 chips | 8542xx (854231 processors, 854232 memories incl HBM, 854239 other ICs), 8541xx discretes, 8523 media | $823B | **yes** (2017-01+) |
| 6 parts & GPU modules | **847330** (also: consumer GPU cards) | $146B | **yes** (2017-01+) |
| 7 baseboards / units | **847180** (HGX trays; purest AI code) | $101B | **yes** (2017-01+) |
| 8 AI servers | **847150** (DGX, assembled systems) | $127B | **yes** (2017-01+) |

Monthly raw pulls cover **all 60 codes across all 8 stages, 2017-01 →
2026-06** (Comtrade batch caches in `data/raw/comtrade_monthly/`, committed:
15.1M rows; TDM fills in git-ignored `data/raw/tdm/`: TWN always, CHN >2024-12,
VNM via VN2 — VN2 confirmed to reach back to 2017). The 2017 sample start
matches the HS2017 vintage of the OECD code list and puts the 2018-19 tariff
war in sample. The reconciled panel covers the same scope — construction,
validation, and audit in section 3 below.

(2024 values CHK basis — China+Hong Kong merged, intra-bloc excluded. The OECD
"photosensitive" basket is deliberately excluded: solar-dominated, a fab output.)

**How stages combine.** The OECD list defines *membership* — which codes belong
to the chain. The stage numbering above is presentation order; the shape is
simpler: two parallel input branches (materials; tools) converge on chip
fabrication, and the output side runs sequentially to servers — drawn with the
codes and 2024 sizes per node in the stylized map below. Stages combine
by three different rules, each with a measured signature
([notes/edge-type-tests.md](notes/edge-type-tests.md); firm-level edge
inventory: [notes/firm-level-supply-chain-data.md](notes/firm-level-supply-chain-data.md)):

- **consumables** (wafers, resists, chemicals → fabs): flow per unit of output;
  contemporaneous with downstream exports (TWN wafer imports vs chip exports:
  r = 0.52 at 0 months, gone by 12);
- **capacity goods** (equipment → fabs): investment building a stock; lead
  downstream exports by 6–12 months in fab countries (TWN peak at +12, KOR at
  +6..12) and must not be treated as current intermediates in chain accounting;
- **kits** (KOR memory + TWN logic converging at advanced packaging): a
  composition fact — cross-destination proportionality 0.83, joint repricing —
  not a monthly-timing fact.

Two things the linear ordering cannot show: the packaging convergence node
sits *inside* Taiwan (why stage charts appear to show Taiwan making chips from
nothing), and design/EDA/IP value enters the chain with no goods flow at all.

![stylized chain topology](https://raw.githubusercontent.com/jasonzhixinglu/global-export-complexity/b67a82a/exports/chain_topology.png)

(Regenerate: `python scripts/draw_chain_topology.py`. Node heights scale with
the log of 2024 world trade — illustrative, so chips does not dwarf raw
materials; stage-table values above are the same numbers unlogged.)

Key facts about the codes: HS6 codes are revision-stable for stages 6–8
(8471.50/80, 8473.30 unchanged HS2012→HS2022) but semiconductor codes diverge
between HS92 and HS2012+ (ICs are 8542.31/32/33/39 in HS2012 vs 8542.11/19 in
HS92) — this forces the HS2012 vintage for anything semiconductor-specific.
Within-HS6 heterogeneity is severe (an H100 module and a commodity part share
847330; exporter unit values within one code span two orders of magnitude) —
see the varieties discussion in [modeling-brainstorm.md](modeling-brainstorm.md).

**Planned basket extensions (Tiers B and C).** Tier B, "AI / data-center
infrastructure" (~$0.45T world 2024) — the rack around the GPU, genuinely
AI-driven but dual-use, to be kept as a separately-labeled basket, never merged
into the silicon tiers: networking/interconnect 851762/851769/851770/854470/
900110, power 850440 (+850423/850434), storage 847170, boards/substrates
853400/853890. Tier C (documented, excluded): lithium batteries 850760, generic
connectors/passives/HVAC — either a different boom (EV/storage) or too generic.
The tiering trade-off: moving outward, the dollar base grows (851762 alone,
$177B, dwarfs the Fed basket) but so does the non-AI share; folding B into A
would turn a clean semiconductor signal into a noisy ICT one. Dual-use is
irreducible at HS6 (data-center vs telecom switches share 851762); the fix is
national HS8-10 lines or firm data. Tier A baskets are implemented in
`src/gec/classifications.py`; B remains a proposal.

## 2. Sources: properties, advantages, disadvantages

| | Harvard Atlas (Dataverse) | UN Comtrade | Trade Data Monitor (TDM) |
|---|---|---|---|
| what | reconciled country×product(×partner)×year files, HS92 + HS2012 vintages | raw national submissions, annual + monthly, API | national customs relayed directly, monthly, API via login |
| frequency | annual | annual + monthly | monthly |
| lag | ~1.3–1.5 years (v18: through 2024, released 2026-04) | ~2–4 months (varies by reporter) | ~1 month |
| reconciled? | **yes** (Bustos–Yildirim mirror reconciliation) | no (as-reported) | no (as-reported) |
| Taiwan | yes (mirror-reconstructed) | **absent** (partner code 490 "Other Asia nes" only) | **yes, direct** (MOF customs) |
| China monthly | — | ends 2024-12 | current (~1 month) |
| Vietnam | yes | monthly ends 2023-12 | `VN2` "(preliminary)" edition, current; runs ~40% below Atlas on 847330 — undercount, use with mirror cross-check |
| quantities | no | netWgt + qty (patchy by reporter) | **yes** (two units: e.g. TWN SET+KG, CHN KG+pieces) |
| complexity (PCI) | **yes** (native) | no (we proxy with Atlas PCI) | no |
| cost / license | free, public | free (registered key for full pulls) | subscription; **raw extracts must never be committed** |
| role here | annual benchmark + upstream stages + validation anchor | monthly backbone (~30 prompt reporters) | gap-filler: TWN always, CHN/VNM recent, laggard top-ups; quantity/unit-value source |

**Atlas** — advantages: the only *reconciled* source (per product-year, country
values sum to world; CIF/FOB handled; reliability-weighted), carries PCI, long
history. Disadvantages: stale (~1.5y), annual only, no quantities; HS92 vintage
unusable for semiconductor codes (use its HS2012 files). Files on disk:
unilateral HS4 (hs92, with PCI), bilateral HS6 (hs92 4 ranges), unilateral +
bilateral HS6 (hs12, 2012–2024). Dataverse IDs in `src/gec/config.py`; next
vintage (through 2025) expected ~spring 2027.

**UN Comtrade** — advantages: free, current-ish, API-scriptable, has the
authoritative *data-availability* endpoint (`/getDA`, no key) to check who has
filed what; monthly bilateral detail; broad reporter set. Disadvantages: raw
(mirror gaps >100% for half of HS6 observations), no Taiwan, heterogeneous lags
(poll before relying: THA was 10 months behind; VNM 2.5 years), recent years
served only in as-reported revision (HS2022-ish). Key limits (free tier): 100k
rows/call, 500 calls/day, keys in `.env` (`COMTRADE_API_KEY`, `_SECONDARY`).
Monthly pull: `scripts/fetch_comtrade_monthly.py` (all 60 codes in seven
density-sized batch groups, all reporters, both flows, quota-aware). Annual HS4 pull with PCI proxy:
`scripts/fetch_comtrade.py` (direct vs mirror per `--mode auto`; mirror = Σ
partners' imports, CIF deflated by 1.10). China files year Y each ~Apr–Jun of
Y+1.

**TDM** — advantages: fastest (~1 month), covers Taiwan directly (the #1
structural gap in public data), two quantity units per record (the unit-value /
terms-of-trade source), national tariff-line capability (relevant for the
varieties validation). Disadvantages: subscription-licensed (raw stays in
git-ignored `data/raw/tdm/`), as-reported, edition quirks (the API spec workbook
in [tdm/](tdm/) is outdated — trust the dashboard dropdown; `VN2` found by
probing; France editions dead on this account), preliminary editions may
under-report (VN2). API: GET endpoint wrapped by `scripts/fetch_tdm.py`
(credentials in `.env`); response is UTF-16 TSV with FLOW/RPT_ISO/PTN_ISO/
COMMODITY/YEAR/MONTH/VALUE/QTY1/UNIT1/QTY2/UNIT2. Standing pulls: TWN full
history, CHN 2024-01+, VN2 full, KR/SG/TH/TR top-ups; portal fallback documented
in [tdm/tdm-report-by-email-help.pdf](tdm/tdm-report-by-email-help.pdf).

**National customs portals** (probed 2026-06, as TDM alternatives/checks):
Taiwan MOF (portal.sw.nat.gov.tw) — free, English, HS2/4/6/8/11, ~10-day lag,
no anti-bot: the clean programmatic option and an independent check on TDM's
Taiwan feed, plus the tariff-line source for the varieties validation. China
GACC (stats.customs.gov.cn) — HS8 exists but behind an aggressive WAF (HTTP 412
on every scripted request); manual-browser only. Vietnam GDVC — reachable but
free data stops at a broad "electronics" group; HS6 is a manual dig.

**Haver** (`emergepr`, tracked in the separate haver-data pipeline; monitoring
only, not basket-grade): curated national aggregates for TW/CN/KR/SG/VN, ~1-2
months fresher than Comtrade, mixed units and concepts. A mapping check found
Vietnam's "Computers, Electronic Products & Parts" ≈ the 8471/8473/8541/8542
HS6 set excluding phones (Haver ≈ 88% of that basket on exports). Taiwan is the
exception worth knowing: emergepr splits IC / DRAM / semi-equipment bilaterally
by partner — finer than HS6.

**Alternatives considered and passed over:** CEPII BACI (reconciled +
quantities, but ~2y stale — superseded by the Atlas+TDM combination); ITC
TradeMap (no advantage over Comtrade for us).

## 3. What we build: the derived datasets

**The monthly bilateral panel** (`data/derived/panel_semi_monthly.parquet`,
build: `scripts/build_monthly_panel.py`; standing per-code validation table:
`results/panel_monthly/build_report.md`; audit record:
`results/panel_monthly/atlas_discrepancy_audit.md`).

Scope: 60 HS6 codes (stages 1-8 above), 30 countries + ROW, monthly, 2017-01
to the balanced endpoint (currently 2026-04; rolls forward on re-fetch). One
reconciled dollar value per exporter x importer x code x month, with both
underlying reports and a provenance tag preserved per cell; 3.5M rows. The
legacy 3-code panel (`panel_ai_compute_monthly.parquet`, 2020+, pre-audit
method) stays on disk for reproducibility of superseded results; everything
new reads `panel_semi_monthly.parquet`.

### 1. Sources and what each contributes

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

### 2. Construction pipeline (`scripts/build_monthly_panel.py`)

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

### 3. Validation against Atlas

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

### 4. Known residual differences and what they mean for analysis

1. **A fairly uniform level offset (~+10% median, +11% aggregate on the CHK
   basis).** Tested, not guessed (audit, final pilots): our monthly sums are
   identical to the annual submissions Atlas ingests (median 1.000, IQR 0.003),
   and the offset is FLAT across mirror-discrepancy quartiles — so it is not
   revisions and not their XXXX trimming; it is Atlas's pair-total blend
   (their estimated CIF deflators and reliability weights vs our measured
   ones), spread uniformly by the proportional rescale. A near-uniform scalar
   cancels in shares and compositions — which is what the factor model
   consumes; we keep the measured parameters.
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

### 5. Regeneration

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

**Annual stage flows** (`dashboard/public/data/techai_bilateral.json`, build:
`scripts/export_tech_bilateral.py` from the hs12 bilateral files): origin ×
destination × stage-basket × year, 2012–2024 — the upstream stages' data and
the flow charts' source.

**Extracts** (`data/derived/bilateral_*.parquet`): per-code slices of the Atlas
bilateral files used by the annual MFMs.

## 4. Quantities and unit values

TDM provides two quantity fields per record (units differ by reporter —
weight nearly always one of them); Comtrade monthly has netWgt/qty but patchy.
Established so far: exporter unit values ($/kg) diverge by 10–100x within a
code and their *dynamics* are the AI fingerprint (TWN 847180: ~$285/kg 2022 →
~$5,900 2026 while generic exporters sat flat). Caveat for any unit-value
index: within-code composition shift and same-good price change are mixed;
separate where quantity units allow. Coverage: full for TDM-pulled reporters
(TWN/CHN/VN2/KR/SG/TH/TR), partial elsewhere.

## 5. Freshness and refresh cadence

| source | cadence | trigger/monitor |
|---|---|---|
| TDM | ~monthly, ~1-month lag | re-run `fetch_tdm.py` (standing set) |
| Comtrade monthly | rolling; reporter-specific lags | re-run `fetch_comtrade_monthly.py` (cached batches skip) |
| panel | after either fetch | `build_monthly_panel.py` (endpoint rolls forward) |
| Comtrade annual | China's year Y lands ~Apr–Jun Y+1 | `fetch_comtrade.py --check` |
| Atlas vintage | ~annual, Apr–Jun, ~1.5y lag | update `DATAVERSE_FILE_ID` in config, re-download |

## 6. Storage and licensing

- `data/raw/` and `data/derived/` are **git-ignored**; everything there is
  downloadable/regenerable. Raw TDM extracts are subscription-licensed and must
  never be committed or published; only derived aggregates enter the repo.
- Credentials (`COMTRADE_API_KEY`, `COMTRADE_API_KEY_SECONDARY`,
  `TDM_USERNAME`/`TDM_PASSWORD`) live in the git-ignored repo-root `.env`.
- Committed artifacts: build reports, results, figures, this documentation.

## 7. Known limitations (the three blindnesses)

Stated fully in [research-proposal.md](research-proposal.md#limitations-we-state-up-front);
in brief: (1) customs sees crossings, not uses — value added is inferred, never
observed; gross flows double-count; IP never appears; (2) within-HS6 varieties
are invisible in values (H100 and commodity parts share codes) — quantities and
national tariff-line data are the partial remedies; (3) domestic transactions
never appear — largest blind spot for the two poles' growing internal loops,
with China's build-out visible only through its input imports.
