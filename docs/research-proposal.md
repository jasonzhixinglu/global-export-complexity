# Research proposal: measuring the global semiconductor trade network in the AI era

## The question, and why now

Between 2023 and 2026 the trade network behind AI computing was rebuilt. Taiwan went
from 10% to 34% of world exports in the compute categories while China fell from 28%
to 12%; the US came to absorb over 40% of world imports; prices per kilogram of the
same customs categories rose up to twenty-fold; and two waves of policy — export
controls and tariffs — tried to redirect the flows. Yet the standard data for
studying this (annual, reconciled, sector-aggregated) lags reality by one to three
years and cannot see any of it happening. We propose a full description and model of
the global semiconductor trade network at monthly frequency, current to within a few
months, with the statistical machinery to say *how the system's structure has
changed*, and a set of network measurements designed for the policy questions this
reorganization raises.

## What we provide

**1. The data infrastructure (built).** A balanced monthly bilateral panel for the
AI-compute goods categories (servers, baseboards, parts/GPU modules): 30 countries
plus rest-of-world, 2020 to within ~3 months of the present, assembled from UN
Comtrade and Trade Data Monitor with Atlas-style mirror reconciliation, per-cell
provenance, and validation against the reconciled annual benchmark (log-correlation
0.94–0.95). This fills the gap between timely-but-raw customs data and
clean-but-stale research data. The chips, equipment, and materials stages are
covered annually today; extending the monthly panel to the chips stage is
mechanical and is the first planned extension.

**2. A dynamic model of the network (built).** Time-varying matrix factor models
(Chen, Chen, Bolivar & Chen 2024) estimated on the monthly matrices: the network
compresses into a few export hubs, import hubs, and a hub-to-hub flow matrix, all
evolving over time. Our methodological additions: an era-anchoring scheme that
makes hub identities stable and comparison across time meaningful (with crosswalk
tables quantifying reorganization at breaks), and a bloc-aggregation design
(China+Hong Kong merged; a US+Mexico variant) that decomposes structural change by
level. Headline findings so far: the network's structure was static through 2022;
its largest break (July 2023) is the H100 shipment ramp — the birth of a distinct
Taiwan factor — and is a demand event, not a policy event; export controls never
appear as structural breaks (their signature is denied growth and within-China-bloc
rerouting), while the April 2025 tariffs are the one policy event that reorganized
the bloc-level structure, coinciding with the appearance of a new Singapore
rerouting factor.

**3. A semi-structural model (sketched below; not yet estimated).** The factor
model is a description, not a mechanism. The simplest model that could *explain*
the dynamics needs only three canonical ingredients — Armington aggregation across
supplier countries, a stage-by-stage production chain, and stage-specific supply
curves — with the key economics carried by two elasticities per stage.

*Setup.* Stages s = 1..S follow the taxonomy (materials → wafers/equipment →
chips → parts → baseboards → servers); countries are indexed o (origin) and d
(destination); time is monthly.

*Demand across varieties (who buys from whom).* Users of stage-s goods in country
d combine country varieties with a CES aggregator,

```
X_s,d = [ Σ_o  a_s,od^(1/σ_s) · x_s,od^((σ_s−1)/σ_s) ]^(σ_s/(σ_s−1))
```

which yields gravity-form bilateral demands

```
x_s,od = a_s,od · ( p_s,o · τ_s,od / P_s,d )^(−σ_s) · X_s,d ,
P_s,d = [ Σ_o a_s,od · (p_s,o · τ_s,od)^(1−σ_s) ]^(1/(1−σ_s))
```

σ_s is the substitutability of suppliers at stage s — how easily buyers reroute.
τ_s,od carries trade costs and policy: tariffs are a τ increase, export controls a
τ → ∞ (or a quantity cap) on specific (o,d) pairs. The taste/technology weights
a_s,od are exactly what the factor model estimates a low-rank representation of:
hubs are blocks of similar a-rows, so the MFM is the model's reduced form.

*Production (how stages connect).* Stage-(s+1) output in country c uses the
stage-s composite plus local factors; the simplest adequate form is Leontief
across distinct input types (a fab needs wafers AND equipment AND materials in
fixed proportions) with the CES aggregation above operating within each type:

```
y_{s+1,c} = A_{s+1,c} · min( X_s,c / λ_s ,  V_c / μ )
```

*Supply (where the bottlenecks live).* Each stage-country pair has capacity k_s,c
and an upward-sloping supply curve whose steepness is the stage's short-run supply
elasticity ε_s:

```
p_s,c = mc_s,c · ( y_s,c / k_s,c )^(1/ε_s) ,        k_s,c(t+1) = k_s,c(t) + investment with time-to-build
```

ε_s is the choke-point parameter: leading-edge fabrication and advanced packaging
have ε ≈ 0 in the short run (output is hard-capped; demand surges go straight into
price), assembly has large ε (Mexico can add shifts), wafers and materials sit in
between. A demand shock at the final stage (AI investment) propagates upstream
through the Leontief links and prices each stage according to its ε_s — which is
precisely the observed 2023–25 pattern: baseboard/packaging prices 20x (ε small),
generic parts prices flat (ε large).

*Identification comes from events we have already dated.* σ_s from observed
rerouting after the April 2025 tariff shock and the export-control episodes
(quasi-experiments with known dates from the factor model's break chronology);
ε_s from the joint price/quantity response by stage to the 2023 demand surge
(price up 20x with quantities capped reveals ε ≈ 0; quantities up with flat
prices reveals ε large). The unit-value data provides p, the panel provides x,
and the era-anchored hubs discipline the a_s,od.

*What it buys.* Counterfactuals the measurement layer cannot produce: the price
and reallocation consequences of removing a node (Taiwan capacity at each stage),
of a tariff schedule, or of capacity build-out (US/Arizona fabs entering k over
time). Estimation is future work; the sketch fixes the target.

*Relation to existing models — and where this one has to differ.* The demand and
network blocks are off the shelf: Caliendo–Parro (2015) is the workhorse for
CES/Armington trade with input–output links and tariff counterfactuals;
Antràs–de Gortari (2020) formalizes multi-stage location choice; Baqaee–Farhi
supply the general nested-CES propagation machinery; Fajgelbaum et al. (2020) and
Amiti–Redding–Weinstein (2019) are the templates for estimating σ off dated tariff
events. But these models carry only *substitution* elasticities (who buys from
whom). Their supply side is flexible — constant returns with mobile factors or
country-level endowments — so no node can cap. Complementarities in the
Baqaee–Farhi tradition mimic bottleneck amplification, but observationally differ
from capacity: under complementarity quantities co-move; under a capacity
constraint the constrained stage's quantity flatlines while its price explodes —
the pattern the data actually shows (baseboards: capped volumes, 20x prices). The
supply block is therefore the contribution: stage-specific capacity with
short-run elasticity ε_s, classically microfounded (a specific-factors production
function y = A·k^α·l^(1−α) gives ε = (1−α)/α — stages differ in how
capital-specific they are) with time-to-build investment. The closest precedent
is Leibovici–Dunn treating chips as a quasi-fixed input in the 2021 auto
shortage — one node, calibrated; here the object is the estimated *profile* of
ε across stages, which is the choke-point map in structural form.

## The measurement program

The organizing idea: the network's *structure* (who trades with whom, how
concentrated, how substitutable) is measurable from flows; its *strains* are
measurable from prices (unit values); and policy impacts are identified by the
dated breaks the factor model provides. Concretely, mapped to the questions we
want to answer:

| # | question | measures | data | status |
|---|---|---|---|---|
| 1 | Terms of trade by country, over time | export vs import unit-value indices per country and stage ($/kg, $/unit); e.g. Taiwan's baseboard export price rose 20x 2022–26 while its input prices did not | TDM quantities (already pulled for TWN/CHN/VNM/KR/SG/TH/TR), Comtrade net weights | raw data in hand; index construction to build |
| 2 | Network dynamics: which linkages intensified | corridor growth rates (TWN→USA 15x, TWN→MEX 6x in one year); hub-to-hub flow matrix F_t; drift statistic dating when structure moved | monthly panel + TV-MFM | built |
| 3 | Centrality, concentration, substitutability | per-stage exporter/importer HHI over time; eigenvector/hub centrality from the flow matrices; substitutability from observed substitution episodes (China→Taiwan share swap; within-bloc reallocation speed after shocks) | monthly panel; annual stage data upstream | straightforward to build on the panel |
| 4 | Fragmentation from tariffs and export controls | within-bloc vs cross-bloc trade shares; the policy-signature contrast (controls: levels and rerouting, no structural break; tariffs: bloc entanglement, new rerouting hubs); counts and sizes of corridors that die or are born around policy dates | TV-MFM eras + panel | core results built; fragmentation indices to formalize |
| 5 | US vs China AI investment, by supply-chain stage | stage-position of each country's imports: China's imports concentrate in fab equipment (upstream capacity building, $79B in 2024, the largest equipment buyer) while US imports concentrate in finished compute (downstream deployment, 40%+ of world server imports); rates of change of each; supplier-diversification (count/HHI of sources) per importer over time | annual stage data + monthly panel | data in hand; comparison to assemble |
| — | choke points | stages that combine high supplier concentration with low observed substitutability and strong price response — the triad that identifies an inelastic bottleneck (candidates the data already suggests: lithography [NLD], wafers [JPN], advanced packaging/baseboards [TWN — the 20x price rise is the smoking gun]; contrast: generic parts, where prices stayed flat because supply was elastic) | unit values + concentration + episode analysis | the paper's flagship synthesis; components exist, assembly to do |

The choke-point logic deserves stating plainly because it ties the program
together: concentration alone does not make a bottleneck (many suppliers are
concentrated but replaceable); a bottleneck is concentration *plus* inelasticity,
and inelasticity reveals itself in prices — the stages where prices exploded when
demand surged are exactly the stages that could not add capacity or be substituted.
Our unit-value data lets us rank stages by that price response and cross it with
concentration, producing an evidence-based choke-point map of the AI supply chain
rather than an anecdotal one.

## What exists, what is next

Built and committed: the monthly panel and its validation; annual and time-varying
factor models with era-anchoring, per-code and bloc variants; the break chronology
and its policy reading; the supply-chain stage map, flow charts and country-network
visualizations; a documented narrative of 2021–26 with all figures reproducible
from scripts.

Next, in order: (i) the network-statistics module (concentration, centrality,
fragmentation indices — mechanical on existing data); (ii) unit-value/terms-of-
trade indices from the quantity data already pulled; (iii) the chips-stage monthly
panel extension (one code-list change to the pipeline; unlocks the upstream half
of the choke-point map and the export-control battlefield); (iv) the value-added
layer (mini-TiVA absorption accounting) that corrects gross-flow importance into
value importance — the Mexico-vs-Taiwan correction; (v) the semi-structural model.

## Limitations we state up front

Customs data measures gross border crossings: the same value is counted at every
hop, entrepots inflate, in-country transformation is invisible, and design/IP —
the largest value component — never appears. Our two-layer design confines these
problems: the measurement layer (panel + factor models) is assumption-light and
stands on its own; the interpretation layers (value-added weights, replaceability
judgments) import assumptions and industry knowledge that are stated explicitly.
Where a claim depends on a judgment — for instance that Mexican assembly is
replaceable and Taiwanese fabrication is not — it is labeled a judgment.
