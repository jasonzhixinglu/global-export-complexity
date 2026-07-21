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

Stated sharply: in a constant-returns, mobile-factor, competitive model, price
responds to demand only through factor and input costs — a few percent in this
episode, against observed unit-value increases of 500–2000% — and quantities
should *rise* with demand, not flatline. No parameterization of that model class
reproduces 2023–25. The one alternative channel, variable markups
(Atkeson–Burstein), is empirically real here — much of the price explosion was
collected as the design layer's margin (Nvidia at ~75% gross margin) while the
physically constrained producer priced modestly — but markups with elastic supply
predict *more* quantity, not rationing and queues. The coherent reading: the
capacity constraint is the root cause, and the markup is how its rent was
collected one layer downstream. Our customs unit values embed the rent wherever
it accrues, so the model fits total chain pricing without claiming who captures
it. A further measurement caveat handled in the terms-of-trade work: part of the
observed unit-value rise is composition within customs categories (PC boards →
H100 boards in the same HS code), to be separated from same-good price change
where quantity units allow.

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

## Rough answers, stated as hypotheses

The questions above are not open-ended: the data already supports first-pass
answers, which the full analysis will confirm, refine, or overturn. Each is
tagged **[measured]** (computed from our data), **[provisional]** (partly
computed), or **[conjecture]** (prior to be tested).

**Where are the bottlenecks?** At and immediately around the fabs. Trade value
exploded for chips and everything downstream while upstream stages grew modestly —
the signature of a constraint at fabrication/advanced packaging: downstream prices
carry the scarcity rent, upstream cannot expand fast enough to matter. Baseboard
unit values 20x'd while generic parts stayed flat, locating the binding constraint
in the Taiwan packaging/systems layer. **[measured]** Markup gains concentrate in
Taiwan and to a lesser degree Korea (memory/HBM), smaller elsewhere.
**[provisional — Korea unit values pulled, not yet indexed]**

**Terms of trade.** Strongly positive for Taiwan (the 20x is the largest
terms-of-trade gain in the sample, plausibly in modern trade data) and Korea;
modestly positive Japan (equipment, wafers). **[provisional]** Ambiguous for
China — its export basket (parts, compliant chips) shows flat unit values while
its import basket (chips, equipment) got pricier, so its ToT may well be
*negative* despite its producer role. **[conjecture — computable from data in
hand]** Negative for pure importers (the US pays the scarcity rents; its ToT loss
is the mirror of Taiwan's gain). **[conjecture]**

**Concentration and near-monopolies.** A nuance the data forces: at the
country-by-HS-basket level, measured concentration is only moderate (2024
exporter HHIs: wafers 0.17 the highest, chips 0.12, fab equipment just 0.085 —
because Japan/US/Netherlands/Germany split the heading). The near-monopolies
everyone knows about — ASML in EUV, Ga/Ge refining, HBM — live at sub-HS6 and
firm level, exactly where limitation 2 blinds us. **[measured, with stated
blindness]** So the honest claim is layered: chips imports (0.165, the China
vortex) and wafer exports are concentrated at country level; equipment is
concentrated at *segment* level, to be shown on the narrower codes (litho-specific
lines) where the data allows.

The deeper point: **concentration is not market power, and the data can tell
them apart.** Mexico has a near-monopoly on server assembly for the US market
(bilateral concentration close to 1), yet almost certainly no pricing power:
assembly is elastic and relocatable, and the two tests agree — Mexico's export
unit values stayed ordinary through the boom (no rent extracted), and its
"monopoly" corridor was contested within a single year (Taiwan's direct server
shipments to the US surged in 2025, something a protected position would not
permit). Japan's wafer dominance is likely the same species: a large share held
by long-term contract producers whose prices moved modestly — positional
concentration in a contestable stage. Taiwan's packaging/systems layer is the
true positive: concentrated AND inelastic AND repriced 20x. The general rule for
the whole analysis: measured concentration (a share) is only the *candidate*
list; market power is concentration times inelasticity, and the price response
under the demand surge is the test that separates them. Bilateral concentration
(who serves whom today) overstates power wherever the stage itself is globally
diversified — assembly runs in Mexico, Taiwan, Vietnam, Malaysia, and Czechia,
so the Mexico–US corridor is a routing choice, not a scarcity. **[measured in
part; unit-value indexing completes it]**

**Fragmentation.** Real but selective, and one prior gets corrected. Weakening
links: China-bloc→US final goods (collapsed in the 2018–19 trade war from $17B to
$7B and never recovered; $6.9B by 2024) and Taiwan→China chips (peak $109B in
2022 → $90B in 2024, the export-control wedge). **[measured]** But the
redirection went to the assembly belt, not to other advanced economies: China-bloc
chips exports to Vietnam quadrupled ($6.7B → $24.5B), while flows to Japan and
Taiwan are flat-to-declining — so the pattern is not "China trades more with
everyone else" but "China's chain re-routes through Southeast Asia."
**[measured — corrects the prior that CHN→JPN/TWN strengthened]** Compliant-chip
carve-outs cut the other way: Taiwan→China *compute-module* flows doubled in
2024–25 even as the chips corridor shrank. Fragmentation is corridor-specific,
not general decoupling.

**US vs China investment.** The cleanest contrast in the dataset: the US buys the
chain's *outputs* (import share of final compute 27% → 40%+), China buys the
*means of production* (fab equipment import share 22% → 26% in 2024, wafer inputs
18% → 24%, with control-deadline stockpiling spikes) while its final-compute share
fell by a third (21% → 16%, still falling through 2026). China remains the
world's assembly floor (~44% of chips imports, flat) — the visible strategy is
substituting imported chips with domestically fabricated ones. **[measured]**
Supplier diversification trends (is each pole concentrating or diversifying its
sources?) remain to compute. **[open]**

A first computed pass of the naive measures — per-stage concentration and
centrality, fragmentation by bloc and by chain position — is documented in
[notes/network-measures-first-pass.md](notes/network-measures-first-pass.md);
headline findings: the authority handoff (every stage upstream of parts drains
into China, every stage downstream drains into the US), the baseboards
concentration spike (exporter HHI 0.38, Taiwan hub score 0.77 — the naive
outlier coincides with the price-confirmed bottleneck), fragmentation as
exclusion from growth (direct pole trade flat in dollars while the network
tripled), and the top-down fragmentation gradient (finished goods aligned with
geopolitics; chips remain the great cross-bloc integrator; upstream tools trade
shows no fragmentation at all).

**The contrasts that carry the story.** Presented as paired differences, the
findings organize themselves:

- *Seller-concentrated upstream, buyer-concentrated downstream.* Upstream stages
  are concentrated on the export side (wafers: exporter HHI 0.17 vs importer
  0.11) — few makers, many buyers; downstream stages flip (chips: importer 0.165
  vs exporter 0.12; final compute: importer-side dominated by one country) — many
  makers, few buyers. The chain runs from near-monopoly at the top to
  near-monopsony at the bottom, and the two poles of concentration are different
  *countries*: sellers' power sits in Japan/Netherlands/Taiwan, buyers' power in
  the US and China. **[measured]**
- *Poles versus connectors versus conduits.* The two poles appear in the data
  mainly as concentrated *buyers* (US downstream, China upstream). The connector
  economies — Taiwan, Korea, Japan — are the concentrated *sellers*, and they are
  exactly where the terms-of-trade gains and markup increases land. The conduit
  economies — Vietnam, Malaysia, Mexico — gained enormous *volume* (the
  redirection and assembly flows) with little visible price gain: quantity share
  without rent. Who you are in the chain determines what you got from the boom:
  buyers paid, sellers earned, conduits grew. **[provisional — conduit unit
  values to be indexed]**
- *Rent follows inelasticity, not volume.* The largest markup and ToT gains sit
  precisely at the stages that are both seller-concentrated and
  capacity-inelastic (Taiwan packaging/systems, Korean HBM), not at the highest-
  volume stages or fastest-growing corridors. This is the choke-point triad
  visible in prices, and the structural model's ε-profile should reproduce it.
  **[provisional]**

## Network measures: what exists, why naive use fails, what we build instead

**The existing toolkit (measures lit review).** *Centrality, for weighted directed
trade networks:* node strength and share-based concentration (HHI); HITS
hub/authority scores (Kleinberg) — the top singular vectors of the flow matrix,
which means our factor loadings, pre-rotation, literally *are* HITS scores, and
the MFM is a multi-factor, time-varying, identity-stable generalization of HITS
(rotated loadings = centrality within named sub-networks; loading row-norms =
rotation-invariant total centrality); PageRank and Katz–Bonacich (with
input–output weights, Katz becomes the Acemoglu et al. influence vector);
betweenness and flow-betweenness (how much trade passes *through* a node);
upstreamness/downstreamness (Antràs–Chor–Fally–Hillberry) locating each country's
average chain position. *Fragmentation:* within-bloc vs cross-bloc trade shares
(IMF, Gopinath et al., blocs from UN-vote alignment); gravity-residual bloc
frictions (the wedge after controlling for size and distance); connector-share
measures (bloc-to-bloc trade routed through third countries — Gopinath et al.
2024); network modularity against the geopolitical partition; and the EU/IMF
"strategic dependency" indicators (import HHI + extra-bloc share +
non-substitutability screens).

**Three failure modes when applied naively — each documented in our data.**

1. *Concentration is not power.* HHI and its relatives rank shares, not the
   ability to move prices. Applied naively they crown Mexico (bilateral
   concentration ≈ 1 on US-bound servers) — a position contested by Taiwan within
   a single quarter and carrying no price premium — and acquit fab equipment
   (country HHI 0.085) where the true near-monopoly (ASML in EUV) hides below
   the HS6 code level. The share is the candidate list, never the verdict.
2. *Even concentration plus inelasticity is not enough — utilization decides.*
   Wafers are concentrated (exporter HHI 0.17, the highest), highly technical,
   and presumably capacity-inelastic; they never became a bottleneck because the
   AI surge is physically narrow (millions of large dies against billions of
   phone chips) and hit during a broader volume downturn, so the stage had
   slack. Rent = concentration × inelasticity × *binding utilization*; any
   metric missing the third coordinate misfires exactly where it looks safest.
3. *Gross-flow centrality rewards pass-through.* Computed on customs values,
   strength, PageRank, and especially betweenness award their highest scores to
   entrepôts and assemblers — Hong Kong and Mexico, the two nodes we can show
   have the least pricing power — because gross flows double-count and
   pass-through *is* betweenness. Naive centrality is close to a paraphrase of
   the Mexico illusion.

**Tailored metrics, each defined by the failure it repairs.** We keep the
standard measures as baselines — the divergence between them and ours is itself
a result — and build:

- a **bottleneck index**: concentration × inverse supply elasticity × utilization,
  with ε from the price/quantity split under the demand surge and utilization
  proxied by volume relative to trend (repairs 1 and 2);
- **rent-weighted centrality**: centrality computed on unit-value *premia*
  (price above the stage's competitive baseline) rather than gross dollars, so
  scores follow where rent is earned, not where boxes cross (repairs 3);
- a **contestability metric**: the observed speed of share reallocation in a
  corridor after shocks — Mexico's server corridor repriced its shares within a
  quarter; a protected position would not — giving an empirical, per-corridor
  substitutability that the EC-style screens assert by assumption (repairs 1);
- **substitutability-adjusted dependence**: import dependence discounted by the
  number of alternative suppliers *with slack*, not just alternative suppliers
  (repairs 2 applied to the buyer side);
- **structural systemicness**: whether a node's removal or a policy shock moves
  the factor *structure* (era break, crosswalk rotation) rather than just
  levels — the measure implied by our structure-vs-flows distinction, with the
  2025 tariff episode as the existence proof.

## Related literature, and an honest account of what would be new

**The strands this work sits between.** (i) *Quantitative trade models*: Armington
and Eaton–Kortum foundations; Caliendo–Parro (2015) adds input–output links and is
the standard tool for tariff counterfactuals, computed as comparative statics
between equilibria ("hat algebra", Costinot–Rodríguez-Clare 2014). (ii) *Global
value chains*: Yi (2003) on vertical specialization, Johnson–Noguera and the OECD
TiVA program on value-added accounting, Antràs–de Gortari (2020) on where each
stage of a chain locates. (iii) *Production networks*: Acemoglu et al. (2012) and
Baqaee–Farhi on how shocks propagate through input networks, quantified for the
pandemic by Bonadio et al. (2021). (iv) *Trade-policy event studies*: Fajgelbaum
et al. (2020), Amiti–Redding–Weinstein (2019) on the 2018–19 trade war — the
template for estimating elasticities off dated policy shocks; a growing
descriptive literature on the 2022+ export controls and "great reallocation"
(Alfaro–Chor 2023) and on fragmentation measurement (IMF). (v) *Supply-chain
resilience theory*: Grossman–Helpman–Lhuillier (2023) on diversification vs
reshoring; Elliott–Golub–Leduc on network fragility. (vi) *Matrix factor
econometrics*: the Chen et al. lineage our estimation builds on, which uses trade
data as an illustration rather than a subject.

**What is securely new but not conceptual: the instrument.** A balanced,
reconciled, monthly bilateral panel of the AI-compute chain, current to ~3 months,
with a stable-labeled dynamic factor structure on top. Nothing comparable is
public. Most of the descriptive results (the pole swap, the price story, the break
chronology) follow from the instrument, not from any conceptual innovation — and
we say so.

**Where there is genuine conceptual scope — two things the literature has not
tried.**

*First: supply-chain adjustment at business-cycle frequency, including rationing.*
The quantitative trade literature is built for comparative statics between annual
equilibria; it has essentially no treatment of how a value chain *transitions* —
at the speed transitions actually happen — when demand outruns capacity: order
backlogs, queues, and above all allocation. In 2023–25 the market for compute did
not clear by price alone: the scarce input was explicitly rationed by its
producers, and which buyers' quantities held up versus which paid higher prices is
visible in our data. Price-clearing CES models have no vocabulary for this.
Modeling — even simply — a chain where one node rations and the rest of the
network adjusts around it, at monthly frequency, against data that actually
resolves the episode, has not been done. The 2023–25 surge is arguably the first
well-measured instance of a major value chain hitting a hard capacity wall, which
makes it the natural laboratory for exactly this.

*Second: policy that changes structure versus policy that changes flows.* Our
empirical finding — export controls moved levels and routes within blocs but never
broke the factor structure, while tariffs produced the one genuine structural
break — points at a distinction the literature does not currently express. In
existing models every policy works the same way (a trade-cost change reallocates
flows smoothly); there is no concept of network *structure* that policy could
break or fail to break, because structure (who co-moves with whom; how many
factors; their composition) is not an object in those models. Formalizing when a
shock reorganizes the factor structure versus merely sliding along it — and which
policy instruments do which — is a conceptual question our two-layer design is
unusually placed to pose, since the factor layer defines "structure" precisely and
the events are already dated.

**What is not new, stated plainly.** Choke-point mapping as an idea (ubiquitous in
the policy literature — ours is *measured*, not conceived); fragmentation indices
(IMF and others — ours are higher-frequency); value-added correction of gross
flows (TiVA invented it — ours would be a monthly miniature); descriptive
reallocation facts (Alfaro–Chor — ours are sharper because the instrument is);
and the ε_s supply block, whose ingredients are classical even if their
stage-level estimated profile is not. The honest summary: one new instrument, two
conceptual openings, and otherwise better measurement of things the field already
wants to know.

## Limitations we state up front

Everything here rests on one observation window: we see goods when they enter and
leave customs, and nothing else. Three distinct blindnesses follow.

**1. We do not observe what products are used for.** A chip crossing into Mexico
might go into a server for the US or a television for Brazil; customs records the
crossing, not the purpose. Value added is therefore never observed — only inferable
by comparing what enters a country with what later leaves it, under stated
absorption assumptions (the Layer-2 program). Gross flows double-count every hop,
entrepôts inflate, and design/IP — the largest value component in this industry —
never crosses a border as goods at all.

**2. We do not observe within-HS6 differences between products.** An H100 module
and a commodity mobile-SoC part can sit in the same six-digit code. Consequences:
level shifts in a code can be composition rather than growth; unit-value changes
mix same-good price change with mix shift (the 20x figures carry both); and the
"AI share" of any code is an estimate, not an observation. Mitigations: quantity
data separates price from volume; the *timing* of composition shifts is itself
informative (a code's $/kg jumping 5x in one year identifies when AI content
arrived); and stage-level contrasts (baseboards vs generic parts) survive because
composition moved in only one of them.

**3. We do not observe transactions that never cross a border.** Multi-stage
production absorbed domestically is invisible: chips fabricated, packaged, and
deployed within China appear nowhere in this data, and the same holds for US
domestic production feeding US data centers. This truncation is not neutral — it
is largest exactly for the two poles, whose domestic loops are growing fastest
(China's fab build-out, US onshoring). Trade data measures the *internationalized
share* of the chain, and that share is itself shrinking at the frontier as both
poles internalize stages. Findings must be read as statements about cross-border
activity, with the domestic loops tracked qualitatively (capacity announcements,
company disclosures) as context.

The asymmetry between the poles deserves its own statement. The US-centered
chain is *internationalized by construction* — fabrication in Taiwan, memory in
Korea, assembly in Mexico and Southeast Asia — so nearly every stage of it
crosses a border and the trade network captures it well. China's frontier effort
runs the other way: SMIC fabrication, domestic packaging, Huawei systems — all
inside one customs territory, invisible here *except at the point of entry*: the
imports of equipment, wafers, and materials that feed it. Two consequences. For
comparisons: like-for-like pole comparisons are biased toward the US chain's
completeness and must say so. For measurement: China's upstream imports are the
observable *leading indicator* of the invisible domestic chain — equipment
bought today is capacity in two to three years — and the framework's testable
implication is that successful domestic substitution must eventually appear in
this data as a *decline in China's chip-import share* (~44% and flat so far)
without a matching decline in its electronics output. Watching that margin is
how a trade dataset monitors a domestication it cannot see.

Our two-layer design confines these problems rather than solving them: the
measurement layer (panel + factor models) is assumption-light about everything it
does claim; the interpretation layers (value-added weights, replaceability
judgments) import stated assumptions and industry knowledge. Where a claim
depends on a judgment — for instance that Mexican assembly is replaceable and
Taiwanese fabrication is not — it is labeled a judgment.
