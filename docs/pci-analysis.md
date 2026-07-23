# PCI workstream: global export market share by product complexity (2000–2024)

> **Scope note (2026-07):** this documents the repo's *original* workstream — the
> PCI/complexity analysis behind the dashboard. The second workstream — the AI
> semiconductor supply-chain project (monthly panel, factor models, network
> measures) — is documented in [data.md](data.md), [research-proposal.md](research-proposal.md),
> [supply-chain-narrative.md](supply-chain-narrative.md), and [modeling-brainstorm.md](modeling-brainstorm.md).
> The two share data infrastructure but are otherwise separate analyses.

A non-parametric analysis of how the world's major exporters are positioned across the
**Product Complexity Index (PCI)**, and how that has shifted over a quarter-century — built so the
estimates respect the trade-accounting identities the data already satisfies.

- **Data:** Harvard Growth Lab, *Atlas of Economic Complexity*, HS92 HS4 `country × product × year`
  ([Dataverse `doi:10.7910/DVN/T4CHWJ`](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/T4CHWJ),
  v18, 2026-04-22). 2000–2024 · 232 economies · 1,243 products.
- **Code:** `src/gec/` (package) + `scripts/` (pipeline). Reproduce everything with
  `python scripts/run_all.py`. All figures below regenerate into `results/figures/`.

> **Exports and imports.** This write-up and the figures use **exports** for concreteness, but every
> estimand below is symmetric: the dashboard runs the identical estimators on `import_value` and
> exposes an **Exports / Imports** toggle. "Market share" then reads as share of world *imports*,
> the distribution as a country's *import* value across complexity, and coverage by top *importers*.

---

## 1. The core problem: smoothing vs. accounting

We estimate two things as smooth functions of complexity:

1. the **distribution of a country's export dollars** across PCI, and
2. a country's **share of world exports** as a function of PCI.

Both must stay consistent with hard accounting facts: a country's dollar-distribution should
integrate to its actual total exports, and market shares summed across countries should be 100% —
not 90% or 110%. Naively, a smoother introduces estimation error that could bias these totals up or
down. The question driving this project was whether that bias exists and how to avoid it.

The answer has three parts, developed below: **(A)** the data is already reconciled upstream, so we
only need to *preserve* identities, not create them; **(B)** for **shares** the right estimator is
*self-calibrating* — adding-up to 100% is exact, by construction; **(C)** for the **dollar
distribution** the total is conserved exactly and the only error is *mean-zero redistribution*
across complexity, which we quantify rather than hide.

---

## 2. Data and how trade databases harmonize it (part A)

Product-level trade data originates in **UN COMTRADE**, where every flow is reported twice — once by
the exporting country, once by the importing partner ("mirror" flows). The two rarely agree:

- **Definitional gap:** imports are valued CIF (incl. freight/insurance), exports FOB. 
- **Reporting error:** at HS6, the mirror gap exceeds 100% for about *half* of all observations.

So raw data does **not** satisfy clean accounting identities. The major databases fix this with
**mirror-flow reconciliation**, done at data-construction time:

- **CEPII BACI** (Gaulier & Zignago 2010): strip the CIF–FOB margin, estimate each reporter's
  *reliability* from how far its declarations sit from its partners', then replace the two
  conflicting figures with a single reliability-weighted reconciled value.
- **Atlas / Growth Lab** (our data) uses the **Bustos–Yildirim** method — the same idea — to clean
  COMTRADE before computing complexity indices.

**Key consequence for us:** by the time we read the file, for each `(product, year)` the sum of
country export values *is* world exports of that product. We are **not** trying to harmonize sources
with a complexity estimator (that would be the ad-hoc move). The estimator's only job is to respect
totals that cleaning already guaranteed. (Caveat: PCI is standardized *within each year*, so
cross-year comparisons are about value-weighted *shifts*, not absolute complexity levels.)

---

## 3. Methodology (parts B and C)

### 3.1 Market share by complexity — a self-calibrating local-linear estimator

For country `c` we estimate its share of world exports near complexity `x`. At product level let
`pci_p`, world value `W_p`, country value `C_p`, and product share `y_p = C_p / W_p`. We fit a
**value-weighted local-linear regression**: at each `x`, a weighted least-squares line of `y_p` on
`(pci_p − x)` with weights `K_h(pci_p − x)·W_p`, taking the intercept. In closed form, with
`S_k = Σ K_h W_p (pci_p−x)^k` and `T_k = Σ K_h W_p (pci_p−x)^k y_p`:

```
ŝ_c(x) = (S2·T0 − S1·T1) / (S2·S0 − S1²)
```

We use **local-linear** rather than **Nadaraya–Watson** (local-constant) because the interesting
variation is in the high-PCI tail near the edge of the data, where local-constant smoothers are most
biased (they flatten toward the local mean at boundaries). Local-linear has lower boundary bias.

**Why shares add to exactly 100% — by construction.** For every product, shares across all
countries sum to 1 (`Σ_c C_p/W_p = W_p/W_p = 1`). Local-linear is a *linear smoother that reproduces
constants* (its normal equations force `Σ_p ℓ_p(x) = 1`). Since the estimator is linear in the
response:

```
Σ_c ŝ_c(x) = Σ_p ℓ_p(x)·(Σ_c y_p) = Σ_p ℓ_p(x)·1 = 1     for every x, any bandwidth.
```

This is the statistical idea of a **self-calibrating / benchmarked estimator** — but here it is
automatic, no adjustment needed. **Verified to `1.1e-14`** at every grid point across all years:

![Adding-up of shares to 1.0](https://raw.githubusercontent.com/jasonzhixinglu/global-export-complexity/main/results/figures/adding_up.png)

The *only* thing that breaks this is clipping individual curves to `[0,1]`, so we store shares
**unclipped** (preserving adding-up) and clip only for display.

### 3.2 The dollar distribution — exact total, mean-zero redistribution

You cannot make a single *smooth* estimate exactly mass-correct on *every* sub-interval; smoothing
redistributes mass. What is guaranteed:

- **Total mass is exact.** A kernel density is a sum of kernels each integrating to 1, so it
  integrates to exactly 1 (→ scale by total exports). Using closed-form Gaussian-CDF bin allocation
  (`estimators.kde_bin_mass`) captures the tails too — total reproduced to relative error `~1e-16`.
- **Sub-range error is redistribution, not net bias.** Over an interval the smooth estimate differs
  from the exact dollars by an `O(h²)·curvature` term that is *signed locally and sums to zero* —
  biased down at peaks, up in troughs. Empirically ~1–2% of total per bin, net bias ≈ 0.

![Mass conservation, China 2024](https://raw.githubusercontent.com/jasonzhixinglu/global-export-complexity/main/results/figures/mass_conservation_CHN.png)

The smooth curve undershoots China's sharp electronics peak (~PCI 0.85) and overshoots its
shoulders; the residuals (bottom) sum to zero. **When exact interval dollars are needed, the
weighted histogram is ground truth** — we never read precise interval values off the smooth curve.

### 3.3 Compact dashboard representation: Gaussian mixtures

The dashboard does **not** ship the smoothed density grid. Each country–year–flow distribution over
PCI is stored as a small **Gaussian mixture** (weights, means, σ) and the curve is reconstructed in
the browser. This is not a different estimator — the value-weighted KDE *is* a Gaussian mixture (one
component per product); we store a reduced K-component version fit to the raw product-level
distribution (`scripts/export_gmm_data.py`).

- **Adaptive K (2–8), per country–flow.** K is chosen by fidelity to the raw distribution (smallest K
  within 0.5 pp KS of the best) and held fixed across years. Commodity exporters land at K≈2, broad or
  bimodal economies at K≈7–8.
- **Temporal stability.** Years are fit sequentially, warm-started from the previous year, so
  components track smoothly instead of swapping. Cold (independent) fitting moves the reconstructed
  curve ~3.8× more frame-to-frame than the truth actually moves; warm-starting brings that to ~0.95×.
- **Smoothness is a render-time blur.** Smoothing a mixture by bandwidth `b` maps `σ_k → √(σ_k²+b²)`,
  so one stored mixture yields the whole Low/Med/High continuum (no per-level storage), and the curve
  is analytic — evaluated on as fine a grid as we like, so it never looks piecewise-linear.
- **Size.** The per-country density payload drops from **3.6 MB → 0.1 MB gzipped (~36×)**.

Market-share-by-complexity is *not* derived this way — it stays the stored local-linear curves
(§3.1). Market share equals the ratio of value densities (the Nadaraya–Watson estimator), and that
ratio matches local-linear to ~0.02 pp; but reconstructing it from the *ratio of two
independently-fit mixtures* is unstable in the thin tails (Gaussian tails don't cancel, the ratio
blows up) and smooths away real fine structure, so the share curves are kept explicit.

#### What the fit error means: KS vs Wasserstein

We measure mixture fidelity against the **raw** product-level distribution (not the smoothed curve),
with two complementary metrics:

- **KS** = max gap between the fitted and empirical CDFs (worst single point) — the *share of value
  misplaced* along PCI.
- **W1** (Wasserstein-1) = `∫|F_fit − F_emp| dPCI` — the transport distance, *how far mass must move*
  (in PCI units).

For the country distributions, median KS is **6.1%** — actually *below* the 6.7% of the KDE curve it
replaced, so on the median country-year the mixture is **more faithful to the raw data** than what we
displayed before. The cost is the worst case: KS p95 ≈ 24%, concentrated on **near-discrete
distributions**. A flow dominated by a single product (e.g. mostly gold or crude oil) is almost a
point mass, and *no* smooth curve — KDE included — can match a vertical CDF step; the mixture diffuses
the spike into a bump.

KS, a sup-norm, is deliberately pessimistic for these cases: the disagreement is a thin band around
the spike, so the **W1 / transport error stays small** — the mass sits in the right place, only
smeared. The economic reading ("this flow concentrates at low/high complexity") survives; what is
lost is the sharpness and the ability to read off the single dominant product.

This is the governing trade-off for the planned **bilateral (origin→destination) view**, where many
corridors are thin and single-product. The same mixture method applies, and the error is driven by
**concentration** (a few products carrying most of the value), not product count. Measured on the
top-30 × top-30 corridors (2022), split by the largest single product's value share:

| top-1 product share | corridors | KS median | KS p95 | W1 median | W1 p95 |
|---|---|---|---|---|---|
| 0–15% (diversified) | 314 | 5.0% | 7.3% | 0.031 | 0.051 |
| 15–30% | 281 | 8.8% | 14.3% | 0.039 | 0.079 |
| 30–50% | 176 | 14.9% | 22.9% | 0.039 | 0.089 |
| 50–100% (single-product) | 99 | 26.8% | 48.1% | 0.036 | 0.105 |

As concentration rises, KS climbs from 5% to 27% but **W1 stays flat at ~0.03–0.04 PCI — the same as
the country-level distributions** (KS 6.7% / W1 0.03). The mixture's *location* of a corridor on the
complexity axis is reliable everywhere; only the *peakedness* of single-product corridors is lost.

The bilateral corridors (top-50 + ROW, 2000–2024) are encoded by `scripts/export_gmm_bilateral.py`
and validated by `scripts/validate_bilateral.py` against the country-level GMMs three ways:

1. **Marginal adding-up** — summing a country's corridor totals over all destinations (incl. ROW)
   recovers its total exports; over all origins, its total imports. Median residual ≈ 0.1%. The tail
   (p95 ~50%) is **commodity exporters with unallocated/confidential partners** (crude oil, minerals):
   the country total counts the flow but the bilateral file cannot attribute it to a destination, so
   the corridor sum understates the *total* (the *shape* is unaffected).
2. **Export–import symmetry** — the inbound corridors of B (column sum over origins) reproduce B's
   independently-reported import distribution at KS ≈ 4%.
3. **Recomposition** — a value-weighted sum of a country's corridor mixtures reproduces its
   country-level distribution at KS ≈ 4% (median), anchoring the corridors to the raw-validated
   country curves.

### 3.4 Where this sits in the literature

The general task — make a model/smoothed estimate respect a known aggregate — is **calibration /
benchmarking** in official statistics: *raking/ratio calibration* (Deville–Särndal), *small-area
benchmarking* (sub-totals must sum to a trusted national total), *time-series benchmarking*
(Denton), *matrix balancing* (RAS/GRAS). For **shares**, local-linear is calibrated for free; for
the **distribution**, calibration pins the *total* exactly (`estimators.calibrate_total`) and the
sub-interval allocation is the irreducible, quantified smoothing trade-off.

### 3.5 Settings (`src/gec/config.py`)

| setting | value | meaning |
|---|---|---|
| `YEARS` | 2000–2024 | analysis window |
| `N_TOP` | 50 | countries tracked for per-country panels |
| `COVER_THRESHOLDS` | 20, 30, 50 | cumulative-coverage thresholds |
| `BANDWIDTH` / `H_DIST` | 0.10 | kernel bandwidth (PCI units), shares / distribution |
| `BIN_WIDTH` | 0.25 | PCI bin width for the conservation diagnostic |

Bandwidth sets the smoothness/redistribution trade-off; the *exact* properties (adding-up, total
conservation) do not depend on it.

---

## 4. Findings

### 4.1 Distribution of export value across complexity

Reproductions of the original notebook charts (CHN/DEU/JPN/KOR, snapshot years), updated to
2000–2024 and the fixed-bandwidth estimator. Normalized *shape*:

![Export complexity density (lines)](https://raw.githubusercontent.com/jasonzhixinglu/global-export-complexity/main/results/figures/repro_density_lines.png)

Same curves scaled to nominal dollars — **area under each curve = that year's total exports**:

![Export value by complexity (lines)](https://raw.githubusercontent.com/jasonzhixinglu/global-export-complexity/main/results/figures/repro_value_lines.png)

All 30 tracked countries as a PCI × year heatmap (per-country normalized):

![Density heatmap](https://raw.githubusercontent.com/jasonzhixinglu/global-export-complexity/main/results/figures/density_heatmap.png)

### 4.2 Global market share by complexity

Full time series, all 30 countries (shared color scale):

![Market share heatmap](https://raw.githubusercontent.com/jasonzhixinglu/global-export-complexity/main/results/figures/market_share_heatmap.png)

Readable snapshots for the major exporters:

![Market share snapshots](https://raw.githubusercontent.com/jasonzhixinglu/global-export-complexity/main/results/figures/market_share_snapshots.png)

### 4.3 Cumulative (stacked) share — CHN + JPN + DEU

Each country's share stacked, by complexity, per snapshot year. The black line is their combined
footprint:

![Stacked cumulative share](https://raw.githubusercontent.com/jasonzhixinglu/global-export-complexity/main/results/figures/stacked_share_by_complexity.png)

The shift is stark: in **2000** the high-complexity share was mostly **Japan + Germany** (~28%
combined), with China concentrated at low PCI. By **2024** China's band dominates almost the entire
complexity range, and the three together reach ~40% at the high-PCI end — but now mostly China.

### 4.4 Coverage: how many countries to "see" world trade at each complexity

![Coverage by complexity](https://raw.githubusercontent.com/jasonzhixinglu/global-export-complexity/main/results/figures/coverage_by_complexity.png)

Mean cumulative world-export coverage by PCI band (`results/tables/coverage_by_pci.csv`):

| coverage | top 20 | top 30 | top 50 |
|---|---|---|---|
| low PCI (≤ −1.5) | 0.51 | 0.68 | **0.83** |
| mid (≈ 0) | 0.76 | 0.86 | 0.95 |
| high PCI (≥ +1.5) | 0.85 | 0.97 | 0.99 |
| overall mean | 0.72 | 0.84 | **0.93** |
| global minimum | 0.45 | 0.63 | **0.81** |

- **Coverage is lowest at low complexity.** "Top-N by total exports" is dominated by manufacturing
  hubs; low-PCI raw materials are exported by commodity economies (ranks #21–50 include
  `BRA, SAU, AUS, ARE, IDN, NOR, QAT, NGA, IRN, IRQ, KWT, CHL`). World trade at low complexity is
  genuinely fragmented across many exporters.
- **Adding countries helps most where coverage is weak:** 20 → 50 lifts low-PCI coverage 0.51 →
  0.83. Top-50 clears 90% across nearly the whole range except the extreme low tail (PCI < −2). A
  clean ">90% everywhere" is not achievable with any modest country count — a structural feature,
  not an estimation artifact.

---

## 5. Caveats

- PCI is standardized within each year → interpret cross-year results as value-weighted *shifts*.
- Shares are clipped to [0,1] for display only; the unclipped surfaces preserve exact adding-up.
- This Atlas vintage re-estimates PCI / rescales `cog`, so values differ slightly from the legacy
  notebook in `legacy/`.
- The extreme high-PCI tail is sparse; stacked/individual curves there are the least reliable.
- The dashboard distribution curves are Gaussian-mixture reconstructions (§3.3), not the raw KDE
  grid. They are faithful in *location* (W1 ≈ 0.03 PCI) but smooth over sharp single-product spikes;
  for exact interval dollars or the dominant product, use the underlying product data, not the curve.

## Sources

- Gaulier, G. & Zignago, S. (2010). *BACI: International Trade Database at the Product-Level.* CEPII
  WP 2010-23. <https://www.cepii.fr/PDF_PUB/wp/2010/wp2010-23.pdf>
- The Atlas of Economic Complexity — data & Bustos–Yildirim cleaning.
  <https://atlas.hks.harvard.edu/data-downloads>
- Harvard Dataverse dataset. <https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/T4CHWJ>
