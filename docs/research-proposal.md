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

**3. A semi-structural model (not started; aspirational).** The factor model is a
description, not a mechanism. A model flexible enough to fit the system and explain
some of its dynamics — capacity constraints at bottleneck stages, demand shocks
propagating upstream, substitution across suppliers under policy — would let the
measurements below speak to counterfactuals. Candidate ingredients: a production-
network structure using our stage taxonomy, capacity/adjustment frictions at the
concentrated stages, and the observed price (unit-value) responses as the
identifying signal for elasticities. This is future work and the proposal's main
open ambition.

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
