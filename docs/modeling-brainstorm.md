# Why we need more than product-level factor models

The argument of this note, in one paragraph: our product-level factor models measure
who ships what to whom, and they do that well. But shipping is not the same as
mattering. In electronics, the country that ships the most valuable boxes (Mexico,
finished servers) often created little of the value inside them, while the country
that created most of the value (Taiwan) can look mid-sized in any single product's
data. So conclusions drawn from one product's model alone can be misleading. To say
who actually matters in this supply chain — and how that is changing — we have to
connect the product layers to each other and weight flows by where value is created.
Some of that can be estimated from our data; some of it requires knowledge the data
does not contain, and we should be explicit about which is which.

## 1. What the product-level models measure

For one product code — say finished servers — the model takes the monthly matrix of
who ships to whom and finds groups of countries that behave similarly as shippers
and receivers (hubs), plus the flows between those groups over time. This is a good
description of one layer of the system. What it cannot be, even in principle, is a
description of the chain that runs *through* that layer: a server shipped from
Mexico contains chips and boards that entered Mexico the month before as imports of
different product codes. Each product model sees one cross-section of that journey.

## 2. How the cross-sections mislead if read alone

Our own results supply the example that matters. In the finished-server data
(847150), Mexico is the largest exporter — $110B over 2020–24 — and in the factor
model it earns its own hub. Taken at face value: Mexico is a pillar of the global
AI-compute trade. In reality, Mexico's role is final assembly — attaching imported
boards to imported chassis. Most of the value in a server leaving Mexico was created
elsewhere: chips fabricated in Taiwan, boards built in Taiwan or Malaysia, design
from the US. The data is not wrong — Mexico genuinely shipped those servers — but
the *importance reading* is wrong.

Three mechanisms cause this, and all are visible in our data:

- **Double counting along the chain.** The same chip is counted once leaving Taiwan
  (as a chip), again inside a board leaving Malaysia, again inside a server leaving
  Mexico. Countries late in the chain ship the biggest dollar totals because their
  boxes contain everyone else's work.
- **Pass-through.** Hong Kong's $59B of "exports" is almost entirely re-export of
  goods it neither made nor changed. The models place it in the core hubs alongside
  actual producers.
- **The bilateral single-hop view.** Taiwan's exports to the US look modest partly
  because Taiwan's output reaches the US *via* Mexico and via assembly in Southeast
  Asia. Its true US-bound share is spread across other countries' export rows.

A practical note: every time the model output was checked against prior knowledge of
this industry (why is Taiwan only 4th in that hub? why does the log transform bury
it?), the discrepancy traced back to one of these three mechanisms. That checking
habit is the right validation method for everything below.

## 3. The question we actually want to answer

"Who matters in the AI-compute supply chain, and how is that changing?" splits into
two different questions:

- **Where is value created?** This is measurable in principle: the value a country
  adds at its hop is (roughly) what it exports minus the inputs it imported for
  those exports. Mexico's markup per server is small; Taiwan's markup per chip is
  enormous.
- **Who is hard to replace?** This is not in trade data at all. Mexico's assembly
  role could relocate in a year; TSMC's fabrication cannot relocate this decade.
  Two countries with the same measured value added can have completely different
  strategic importance. Answering this requires outside knowledge — technology,
  capital intensity, lead times — imported explicitly as context, not inferred.

Keeping these separate matters, because the data can correct the Mexico illusion for
the first question but only informed judgment answers the second.

## 4. What connecting the layers requires

Three ingredients, in increasing order of difficulty:

1. **The chain order.** Chips → boards/parts → subassemblies → finished systems.
   We already have this: it is the taxonomy (docs/data.md §1), and it is
   knowledge about the products, not something estimated.
2. **Tracking flows through countries.** How much of Mexico's server exports is
   Taiwanese board content? Not directly observed — customs data records shipments,
   not what happens inside the country between arrival and departure. It has to be
   estimated by comparing what goes in (imports of upstream codes) with what comes
   out (exports of downstream codes), country by country, with a lag. This is where
   assumptions live: how imports map to exports when a country has several output
   products, how long goods sit in inventory. Existing frameworks (the OECD's
   value-added accounting) solve this with a proportionality assumption at annual
   frequency; at monthly frequency it is harder and this is the genuinely new work.
3. **Value-added weights at each hop.** The difference between the value of what a
   country ships and what it imported to make it. Our data has raw material for
   this: values and quantities (so unit values), and for pass-through hubs, actual
   re-export statistics (Hong Kong publishes them).

With those three, the correcting objects become computable: e.g. "Taiwan-origin
content of US server imports, monthly" — which would show Taiwan's true weight
regardless of which country's flag is on the final box, and would show whether the
2025 tariff shock actually rerouted chains or just relabeled them.

## 5. The plan: two layers, and honesty about what each can claim

- **Layer 1 (built): the per-product factor models.** Good measurement of each
  cross-section: hubs, memberships, flows, and the dates when structure broke
  (mid-2023, spring 2025). These results stand on their own and involve no
  assumptions about how products relate.
- **Layer 2 (open): the chain accounting.** Connect the layers using the three
  ingredients above. Its outputs re-weight Layer 1's story: gross-flow importance
  becomes value-added importance. Every Layer 2 claim depends on the absorption
  assumptions, so they must be stated and stress-tested — and claims about
  *replaceability* (question two above) additionally depend on imported industry
  knowledge and should be labeled as judgments, not estimates.

Shelved along the way: a tensor factor model over exporter × importer × product.
Rejected because it assumes countries in the same hub export the same product mix,
when the defining feature of real supply-chain blocs is the opposite — members
divide the labor (Taiwan boards, Korea memory, Malaysia assembly). Our per-code
results confirm the mixes differ: the server network is Mexico-led, the board
network Taiwan-led, the parts network China-led.

## 6. Test cases the finished system must get right

The calibration standard: the system is judged against what we know about this
industry. If it fails these, the model is wrong, not the priors.

| country | gross-flow picture (Layer 1) | true role the system must recover |
|---|---|---|
| Mexico | top server exporter, own hub | low-value final assembly; large flows, small value added, replaceable |
| Taiwan | mid-ranked in several codes | dominant value creator; its content reaches the US mostly via others' exports; hard to replace |
| Hong Kong | core-hub member, big flows | pass-through; near-zero value added |
| Vietnam / Malaysia | rising exporters | assembly tier: genuine but thin value added, growing |
| China | biggest parts exporter | mixed: assembly AND growing value creation AND a major final destination — the one case that needs care rather than a label |

---
*Working decisions (details in results/mfm/ and the git log): dollar levels rather
than logs; 12-month trailing estimation window; no seasonal adjustment; era-anchored
hub labels with breaks at 2023-07 and 2025-04.*


## 2026-07: Visualization — country-node network graphs (OPEN)

The staged flow-of-funds charts have a structural limit: columns imply goods hop
countries between stages, but integrated assemblers (Mexico: chips in, servers
out) do the intermediate stages domestically, which customs data cannot show. A
complementary chart type would put COUNTRIES as nodes (one node per country, laid
out geographically or by role) and draw product flows as directed edges between
them, coloured/styled by product stage — so a country's full input/output mix sits
at one node instead of being scattered across checkpoints. Candidate first cut:
top ~12 countries + Other, edges from the same stage flow data, edge width = $.


## 2026-07: What the hubs actually identify — latent varieties within codes

**The puzzle.** If goods within an HS6 code were homogeneous, gravity logic says
every exporter should have roughly the same destination profile (proportional to
demand and distance) and roughly one world price. Neither holds. Destination
profiles separate into sharp hubs, and — the decisive evidence — exporters of the
"same" code sell at unit values spanning two orders of magnitude *in the same
year*:

| $/kg, 2025 exports | 847330 (parts) | 847180 (units) | 847150 (servers) |
|---|---|---|---|
| China | 58 | — | — |
| Turkey | 89 | 92 | 285 |
| Thailand | 132 | — | — |
| Korea | 5,071 | 356 | 274 |
| Taiwan | 280 | 3,646 | 1,678 |
| Singapore | 668 | 5,828 | — |

And the dynamics split the same way: Taiwan's 847180 went from ~$285/kg (2022)
to ~$3,646 (2025) while Turkey's stayed near $92 — the AI variety appreciated
13x, the generic variety did not move.

**The interpretation.** The factor model, fed only flow patterns, is recovering
*variety-market segments*: clusters of exporters that make similar sub-products
and therefore sell to similar customer sets. Hub loadings are variety-mix
memberships; the hub-to-hub matrix F is demand flowing between variety segments.
This explains at once why hubs are so clean (varieties differ physically, not
just statistically), why hub membership predicts price tier (China's parts hub at
$58/kg vs the Taiwan module complex at 10-60x that), and why the 2023-07 break
was Taiwan's hub "purifying" — a new variety (AI hardware) coming into existence
inside old codes.

**Structural mapping: hubs as discovered Armington nests — with a two-type
refinement.** Standard Armington assumes each country is its own variety. The
evidence suggests varieties exist at a coarser level that hubs approximately
recover — but hubs come in two types, and the substitution evidence separates
them. Some hubs partition *varieties* (847180: the solo-Taiwan hub owns the AI
baseboard; nobody substituted away from it at any price — low cross-nest
sigma). Other hubs partition *locations of the same variety* (847150: the
MEX-led and TWN-led hubs both ship AI servers, and Taiwan took Mexico's US
share within a quarter — the fast substitution ran ACROSS those hubs, because
they are one variety in two places). So the correct statement is: substitution
is fast within a variety regardless of hub, and slow across varieties; hubs
recover the variety partition only where production is geographically
concentrated. The supply elasticity ε still applies at the variety level:
capacity bound for the AI variety of 847180 while the generic variety in the
same code stayed slack.

**Testable implications.**
1. National tariff-line data (Taiwan and US publish 8-11 digit lines) should
   decompose these codes into sub-lines that align with hub membership — the
   direct confirmation, and a natural appendix exercise.
2. Unit values should cluster within hubs and diverge across them (the table
   above is the first pass; more reporters via TDM would fill it out).
3. Substitution speed should be fast within a VARIETY and absent across
   varieties — both observed (MEX->TWN server assembly contested in a quarter;
   TWN baseboards never substituted). Note the server case is cross-hub
   substitution within one variety: hub != variety there (see refinement above).
4. Price dynamics should track the variety, not the code — observed (TWN vs TR
   in 847180).

**Evidence status (honest audit, 2026-07).** Established: within-code exporter
heterogeneity (unit values 10-100x apart, necessary condition); coarse
hub/price-tier alignment (CHN's cheap-parts hub vs TWN elsewhere; solo-TWN
847180 hub = the price outlier); and the temporal coincidence — flows (hub
purification) and prices (unit-value divergence) independently date the AI
variety's birth to mid-2023. Known counterexample: KOR ($5,071/kg) and TWN
($280/kg) shared an 847330 hub — within-hub heterogeneity remains large, so
hubs are coarse variety clusters at best. Untested: the direct tariff-line
decomposition (Taiwan 11-digit) and a formal within/across-hub unit-value
variance decomposition (needs more reporters' quantities).

**Consequence for measurement.** The effective market is the variety segment,
not the HS6 code. Concentration and power computed at code level understate
whenever a hub owns a variety: 847180's exporter HHI of 0.38 already flags
Taiwan, but the AI-baseboard *variety* within it is closer to a Taiwan
near-monopoly. Hub-level (variety-level) concentration is the right metric, and
the factor model provides the partition to compute it on.
