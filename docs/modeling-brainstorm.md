# Modeling notes: what we estimate, what it means, what we decided

The project's consolidated interpretation and decision record. Superseded
intermediate discussions (this document developed through many revisions) live
in git history; what follows is the settled state as of 2026-07, organized as:
the measurement problem (I), the architecture and decisions (II), what the
factor model identifies (III — the main synthesis), calibration test cases
(IV), and open items (V).

---

## I. The measurement problem: shipping is not mattering

Product-level trade data measures who ships what to whom, and our models
describe that well. But gross flows mislead about *importance* through three
mechanisms, all visible in our data:

- **Double counting along the chain**: the same chip is counted leaving Taiwan,
  again inside a board leaving Malaysia, again inside a server leaving Mexico.
  Late-chain countries ship the biggest totals because their boxes contain
  everyone else's work.
- **Pass-through**: Hong Kong's ~$59B of "exports" is mostly re-export of goods
  it neither made nor changed.
- **The single-hop view**: Taiwan's exports to the US look modest because its
  content reaches the US via Mexico and Southeast Asia, spread across other
  countries' export rows.

The canonical example: Mexico is the largest server exporter ($110B 2020–24)
and earns its own factor — yet its role is final assembly of imported content.
The data is right; the naive importance reading is wrong. "Who matters" splits
into two questions: *where is value created* (estimable, under stated
absorption assumptions) and *who is hard to replace* (not in trade data;
requires labeled judgment — though the price-response evidence now answers it
partially: see the market-power results in the research proposal).

## II. Architecture and standing decisions

**Two layers, assumptions quarantined.** Layer 1 (built): per-product factor
models — assumption-light measurement of each cross-section; hubs, flows,
break dates. Layer 2 (open): chain accounting connecting the layers (absorption,
value added) — all cross-product assumptions live here and are stated
explicitly. A reader who rejects Layer 2's assumptions still gets Layer 1.

**Decisions log** (rationales in git history and results/mfm/):

| decision | choice | reason |
|---|---|---|
| transform | dollar levels, not logs | logs bury scale (demoted Taiwan); the paper's own application uses levels |
| estimation window | 12m trailing, uniform | seasonally balanced, one-sided (defined to the last month); OOS-validated vs 6/18/24m |
| seasonality | none removed | 12m window absorbs it; LNY handled by presentation (3m MA) |
| hub labels | era-anchored (constant anchors within calm eras; Procrustes to anchor; crosswalks at breaks) | chained matching accumulates ambiguity exactly at the breaks |
| blocs | CHN+HKG merged (CHK) as the preferred basis; USA+MEX variant as diagnostic | entrepôt churn nets out; **Taiwan is never merged into a China bloc** (its substitution vs China is a finding, not noise) |
| tensor factor model (exporter×importer×product) | **shelved** | Tucker separability forces same-hub countries to share product mix; real blocs divide labor (memory vs boards vs assembly) |
| rank | k=r=4 working rank (ratio estimator picks 1 = gravity factor) | the hub structure lives at the 2nd spectral tier |

## III. What the factor model identifies (the synthesis)

### 1. Relative to vector PCA: one added restriction

The MFM is vector factor analysis on the 900 corridor cells plus one
constraint: loadings are separable, Λ = C ⊗ R — corridor (i,j) loads only
through i's exporter type and j's importer type. Corridors have no identity of
their own. This is a bilinear, gravity-shaped restriction on comovement; it is
also exactly a low-rank structure on the Armington weight matrix, which makes
the MFM the reduced form of the structural sketch (research-proposal §3):
writing gravity demand as x_od,t = A_od·φ_o,t·ψ_d,t with A low-rank *is* the
time-varying MFM. Hence: hub counts = rank of A; loading subspaces = type
spans (tilted by relative prices — so breaks = changes in A or large price
divergence; 2023-07 was both); F_t = type-pair expenditure aggregates.

### 2. The interpretation: factors are demand programs

The settled reading, reached after several refinements (varieties → co-demand
clusters → composite bundles → programs): **each factor is a spending stream**
— a recurring pattern of expenditure over destination×month. Concretely: the
*AI build-out program* (US-concentrated expenditure, flat until mid-2023 then
growing ~8x) and the *China assembly program* (stable component-buying spread
over KOR/VNM/MYS). With natural normalizations:

- **exporter weights = supplier market shares within a program** (cents of
  each program dollar going to each country);
- **importer weights = where the program's spending sits**;
- **F_t = the programs' budgets month by month**;
- **a country's loadings = how much of its exports each program finances.**

The 2023-07 structural break, restated: *a new spending program entered the
economy*, and the factor model watched its column appear.

### 3. Below the factorization's resolution: supply structure within programs

Programs are demand objects; the factorization is agnostic about the *supply*
structure behind each. Three types occur, with discriminators and evidence:

| program's suppliers are… | example | discriminating evidence |
|---|---|---|
| a **sole source** | 847180: solo-Taiwan (AI baseboards) | trivially identified; no substitution at any price; the 20x unit-value spike |
| **substitutes** (same product, multiple locations) | 847150: MEX and TWN assembling AI servers | ~zero monthly timing correlation but monotone share reallocation (TWN share of the pair to the US: 25%→47% in 3 years) |
| **complements** (a kit consumed together) | 847330: KOR memory + TWN modules | cross-destination proportionality corr(log,log)=0.83; growing intra-pair trade (KOR→TWN 4x); joint repricing under the common bottleneck; monthly changes anti-correlate at big destinations (consistent with lead–lag shipping; lagged test pending) |

Working rules: substitution is fast within a product regardless of factor
assignment, slow across products, near-zero within kits; a bottleneck in one
kit member caps the whole kit (demand complementarity operating *inside* a
program, on top of the capacity story). Unit-value caveat: $/kg confounds value
density with physical form (bare HBM at $5,071/kg vs assembled modules at
$280/kg can be the *same* program) — cross-form comparisons need per-unit
quantities. Within-code heterogeneity is severe regardless (same-code exporter
unit values span 10–100x): HS6 codes bundle different products, and the
factorization sees through the codes to the programs.

### 4. Identification: why the basis is not a convention here

Pure algebra leaves total rotational indeterminacy (only the subspace is
identified). Economics adds **nonnegativity** — market shares and budgets
can't be negative — which converts the problem from PCA to NMF, where
uniqueness theorems exist. Geometrically: the data points must lie inside the
cone of the program profiles, and the profiles inside the positive orthant;
the edges are pinned when data points press against them — i.e. when near-pure
rows/columns exist.

Status, demonstrated then stated:

- **Numerically unique**: choosing the basis by minimizing negative mass over
  rotations (60 multi-starts, per code, both sides) converges to a single
  solution (dispersion 0.000) — and that solution **is the varimax basis**
  (column match |cos| 0.99–1.00), so every hub result in the project is the
  admissible basis. Residual ~1% negativity is the orthogonality tax; tri-NMF
  (Route B) would remove it without moving the basis.
- **The applicable theorem is near-separability (anchors)** — the strongest
  condition — and it holds on *both* sides where one suffices: measured
  own-purity of each program's top participant is 0.93–1.00 (TWN, MEX, CHK,
  VNM on the supplier side; USA, CHK on the buyer side). Trade translation:
  each spending stream has a country supplying essentially nothing else
  (GVC specialization), and a buyer whose purchases are essentially only that
  stream (the US *is* the AI program's buyer). The weaker
  sufficiently-scattered condition (sparse program membership despite dense
  bilateral totals — which reconciles identification with gravity) is implied.
- **Epistemic chain for the paper**: condition stated → trade meaning →
  empirical signature measured → uniqueness demonstrated → external
  certificates (Taiwan tariff-line decomposition; CES loading–price test)
  specified but not yet run. Same status as topic-model anchor identification;
  apparently the first application of that machinery to trade factorization.

### 5. Consequences for measurement

The effective market is the program/variety, not the HS6 code: concentration
and market power computed at code level understate wherever a program has a
sole source (847180's HHI 0.38 already flags Taiwan; the AI-baseboard program
within it is closer to a monopoly). The factor partition supplies the market
definition the power metrics should run on. And the within-kit elasticity is
identifiable from loading–price comovement (shares rising in a component's
price ⇒ complements), a route neither flows nor prices alone provide.


> **Estimation vintage note (2026-07).** Figures in this section that come from the monthly panel were computed on the pre-audit 3-code panel (2020+). The audited 60-code panel (docs/data.md §3) and re-estimated TV-MFM confirm the qualitative test-case results; exact panel-based numbers are queued for re-verification. Atlas-based figures are unaffected.

## IV. Test cases the finished system must get right

Judged against industry knowledge; if the system fails these, the model is
wrong, not the priors. Status added as of 2026-07:

| country | gross-flow picture | true role | status |
|---|---|---|---|
| Mexico | top server exporter, own factor | replaceable low-value assembly | **confirmed by data**: no price premium; corridor contested by TWN within a quarter |
| Taiwan | mid-ranked in several codes | dominant value creator, hard to replace | **confirmed**: 20x repricing; sole-source program; no substitution |
| Hong Kong | core-hub member | pass-through | **confirmed**: netted out by CHK bloc; conduit-index signature |
| Vietnam/Malaysia | rising exporters | thin-margin assembly tier, growing | consistent (volume without price gains); ToT indexing pending |
| China | biggest parts exporter | assembler AND value creator AND main non-US buyer | the one case needing care; upstream-import surge = capacity build-out (leading indicator) |

## V. Open items, in rough priority order

1. **Taiwan tariff-line decomposition** (free 11-digit customs portal): the
   direct external certificate for program identification; highest
   evidence-per-effort available.
2. **CES loading–price test**: second certificate; also identifies within-kit σ.
3. **Lagged cross-correlation** of kit co-shipment (memory leads modules?).
4. **Per-unit unit values** (QTY1) for cross-form price comparisons; more
   reporters for the within/across-program variance decomposition.
5. **True NMF fit (not just rotation)**: the current basis is spectral
   estimation followed by rotation *within the spectral column space* to the
   most-nonnegative basis — we never actually fit an NMF, and a genuine one
   (multiplicative updates / HALS) is free to leave that subspace. Fit it,
   compare fit quality and hub compositions against rotate-then-clip;
   agreement vindicates the cheap spectral route, disagreement is a finding.
   Subsumes the tri-NMF (Route B) idea.
6. **Concentration-vs-power exercise**: compute upstream (origin) and
   downstream (destination) concentration per segment via the measures in
   [concentration-fragmentation-nnf-mfm-trade.md](concentration-fragmentation-nnf-mfm-trade.md)
   (implemented: `scripts/network_stats.py` -> results/network_stats/) and
   test whether they predict where pricing power actually showed up
   (Taiwan yes, Mexico no). Divergence localizes the substitution
   elasticities.
7. **Layer 2 chain accounting** (mini-TiVA absorption): the Mexico-vs-Taiwan
   correction as estimates; monthly proportionality assumptions are the new
   work. Constraint from the edge-type tests (docs/notes/edge-type-tests.md):
   equipment flows are investment, not intermediates — absorb consumables
   contemporaneously, capitalize equipment (its 6–12 month lead in fab
   countries also yields a capacity-stock proxy series).
8. ToT indices per the research-proposal roadmap.
