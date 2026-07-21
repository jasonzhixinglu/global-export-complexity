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
| 1 raw materials | 280461 silicon, rare gases 280421/29, Ga/Ge/In 282560/8112xx, chemicals | $13B | no (annual) |
| 2 wafers & inputs | 381800, 3701xx/370790 | $25B | no |
| 3 litho & optics inputs | 9001xx/9002xx, 901210/90, 903141 | $38B | no |
| 4 fab equipment | 8486xx, metrology 903082/84/9033, fab plant | $244B | no |
| 5 chips | 8542xx (854231 processors, 854232 memories incl HBM, 854239 other ICs), 8541xx discretes, 8523 media | $823B | no (extension planned) |
| 6 parts & GPU modules | **847330** (also: consumer GPU cards) | $132B | **yes** |
| 7 baseboards / units | **847180** (HGX trays; purest AI code) | $73B | **yes** |
| 8 AI servers | **847150** (DGX, assembled systems) | $117B | **yes** |

(2024 values CHK basis — China+Hong Kong merged, intra-bloc excluded. The OECD
"photosensitive" basket is deliberately excluded: solar-dominated, a fab output.)

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
Monthly pull: `scripts/fetch_comtrade_monthly.py` (4-month batches, all
reporters, 3 codes, both flows). Annual HS4 pull with PCI proxy:
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

**The monthly bilateral panel** (`data/derived/panel_ai_compute_monthly.parquet`,
build: `scripts/build_monthly_panel.py`; report:
`results/panel_monthly/build_report.md`):

- **Scope:** 30 countries + ROW, codes 847150/847180/847330, 2020-01 → balanced
  endpoint (currently 2026-04; rolls forward on re-fetch).
- **Sources & hierarchy:** Comtrade backbone; TDM where Comtrade is silent
  (TWN always; CHN > 2024-12; VNM; laggard top-ups). Comtrade beats TDM when
  both report the same flow.
- **Reconciliation (simplified Bustos–Yildirim):** each corridor-month observed
  up to twice (exporter FOB, importer CIF/1.10); both present → mean + recorded
  mirror gap; one → that one. Per-cell provenance. Taiwan partner code 490
  mapped to TWN.
- **Balanced endpoint rule:** last month every kept country reports on some
  side; stragglers (FRA + 1-month laggards) covered by mirror, their ROW cells
  dark and flagged.
- **Validation:** aggregated to annual vs Atlas bilateral 2020–24:
  log-correlation 0.94–0.95, median ratio ~0.92–0.95 per code.
- ~205k rows; ~6–7 MB/code as CSV.

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
