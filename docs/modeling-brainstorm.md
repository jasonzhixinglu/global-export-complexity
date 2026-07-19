# Modeling brainstorm — beyond the per-code matrix factor model

Running notes on modeling directions considered for the TV-MFM project: what was
considered, why it was adopted/shelved, and what would trigger a revisit. Newest at
the bottom; add dated sections as discussions happen.

## 2026-07: Tensor (Tucker) factor model over exporter x importer x product — SHELVED

**The idea.** Extend `Y_t = R F_t C' + E_t` to a 3-way Tucker factorization
`Y_t = G_t x1 A1 x2 A2 x3 A3 + E_t` where mode 3 is the HS6 product dimension:
export hubs (A1), import hubs (A2), product baskets (A3), and a core tensor G_t of
hub-to-hub flows per basket. Estimation is a mode-wise generalization of the current
machinery (unfold, pooled second moments, top eigenvectors per mode) — everything
built for the matrix case (12m windows, era anchoring, varimax, crosswalks) ports.
Reference: Chen, Yang & Zhang (JASA 2022), TOPUP/TIPUP estimators (Han-Chen-Zhang).

**Why shelved: Tucker separability contradicts how the baskets work.** In Tucker, a
country's export composition over products is fully determined by its hub-membership
vector: countries loading on the same single hub are forced to export the *same
product mix* (differing only in scale), because loadings interact across modes only
through the core. But real supply-chain blocs feature *complementary* specialization
— within one bloc, Taiwan supplies boards, Korea memory, Malaysia assembly. A hub
whose defining feature is internal division of labor is structurally invisible to a
separable factorization; the specialization gets dumped into the error tensor. The
escape (rank-inflating A1 until each big exporter is its own hub) re-derives
"separate per-code models" with extra notation.

**Empirical support for the objection:** the per-code annual MFMs found materially
different hub structures per product — 847150 is MEX-led (server assembly), 847180
TWN-led (baseboards), 847330 CHN-led (parts). Non-separability is in the data.

**Revisit if:** a wider product panel (e.g. OECD semiconductor value-chain codes)
reveals *blocks* of codes that do share exporter structure — then one Tucker model
per block could be right-sized.

## 2026-07: Why no off-the-shelf model fits the product dimension

Factor models treat each mode's coordinates as exchangeable; the product dimension
here is *ordered* — a production chain (chips -> boards/parts -> trays -> servers).
The economically meaningful cross-product coupling is directed and cross-sided:
a country's **imports** of the upstream code become its **exports** of the
downstream code with a lag. That dependency (import side of one layer -> export side
of another) is not expressible in any symmetric low-rank decomposition, and its
direction is domain knowledge (HS taxonomy + engineering reality), not something
contemporaneous covariance can identify. Nearest off-the-shelf relatives (multilayer
/ inter-layer stochastic block models) target community detection, not valued,
directed, time-varying flows with a chain ordering.

## 2026-07: Candidate architecture — measurement layer + chain-coupling layer (OPEN)

- **Measurement layer (built):** per-code TV-MFMs with era-anchored hub labels.
  Imposes nothing across products; defensible given non-separability.
- **Structure layer (idea):** model coupling *between* per-code estimates with the
  chain ordering imposed from context: country i's import loading on upstream-code
  hubs at t vs its export loading on downstream-code hubs at t+lag. Existence proofs
  in current results: MEX (top 847330 parts importer, top 847150 server exporter),
  VNM similarly. Estimated across countries/time, this yields each country's
  *chain position* and how positions migrated at the era breaks (did 2023-07
  propagate upstream-first? did 2025-04 tariffs reroute the parts->systems link from
  CHN to MEX?). Era-anchored labels make cross-code correlation of loadings
  meaningful. Likely novel: "value-chain coupling of factor loadings across product
  layers" does not appear to exist in this literature.

**Status:** open idea, unprototyped. Minimal first test: scatter of countries'
847330 import loadings vs 847150 export loadings by era, before building anything
dynamic.

## 2026-07: Multi-hop supply chains — a stage-layered flow-tracing model (OPEN)

**The gap.** Bilateral flows per code describe single hops. The real object is a
multi-hop chain crossing several countries and *several product codes* as value is
added: semiconductor inputs leave TWN -> assembly in MYS/VNM (leaves as boards,
847330) -> systems integration in MEX (leaves as servers, 847150) -> US data center;
plus pure transshipment hops (same code re-exported, HKG/SGP). No single-code
matrix, and no cross-code factor coupling, represents a *path*.

**The borrowable framework: trade-in-value-added accounting** (OECD TiVA / WIOD /
ADB MRIO). Its architecture: (1) inter-country flows per sector (observed);
(2) within-country absorption coefficients -- how imports of upstream sectors enter
production of downstream outputs; (3) a Leontief-type inversion that turns one-hop
flows + absorption into ultimate origin->final destination content. Not usable
directly: annual, 2-3y lag, sector-level (all of computers+electronics is one cell).
But the architecture ports to our monthly HS6-stage panel.

**Sketch: a mini-TiVA at stage granularity, monthly.**
- *Layers* = production stages from docs/tech-ai-taxonomy.md (chips 8542/8541 ->
  parts/boards 847330 -> units 847180 -> systems 847150), i.e. the ordered context
  the factorization discussion said was required.
- *Within-stage edges* = our observed bilateral monthly flows per stage (the panel;
  chips layer would need adding -- codes exist in the taxonomy).
- *Cross-stage edges (the modeled part)* = within-country absorption: country c's
  stage-s imports absorbed into its stage-(s+1) exports. Identification options, in
  increasing ambition: (a) TiVA-style *proportionality assumption* (imports of stage
  s are absorbed proportionally across all of c's stage-s+1 outputs); (b) calibrate
  levels with lagged import->export regressions per country (the chain-coupling
  layer above becomes the estimator of absorption intensities); (c) sanity-bound by
  value-added markups (unit values / quantities are in the TDM pulls).
- *Transshipment vs transformation*: same-code re-export needs separate treatment
  for entrepots. Data exists: HKG publishes re-export statistics explicitly;
  Comtrade has re-export flow codes for some reporters; TDM's Additional Data
  Fields include re-export flags for some countries.
- *Output objects*: absorbing-Markov / Leontief walk through the layered graph ->
  monthly "ultimate content" matrices, e.g. the TWN-origin share of US
  systems-imports by month, or the distribution of hop counts and routes for a
  dollar of stage-1 exports. Era-dated rewiring of *routes* (not just bilateral
  intensities) becomes measurable: did 2025-04 tariffs reroute the MYS->MEX->USA
  path around CHN?

**What it needs that we have:** the stage taxonomy, the monthly panel machinery
(extending to the chips layer is a code-list change), quantities for markup checks,
HKG re-export ratios (public).
**What it needs that is genuinely new:** the absorption identification (the
proportionality assumption is the standard crutch and is strong at monthly
frequency), and inventory/timing slack between import and re-export hops.
**Relation to the MFM:** complementary, not competing -- the MFM describes each
layer's network structure; this describes flow *through* layers. The era breaks
found by the MFM are the natural hypothesis dates for route rewiring.

**Status:** open; the biggest missing ingredient is a defensible absorption
identification. Cheapest first probe: pick the single best-instrumented path
(TWN chips -> MYS/VNM boards -> MEX/USA systems) and check timing + magnitude
consistency in the raw panel before formalizing anything.
