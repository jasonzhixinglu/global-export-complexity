# Network measures on the AI-compute chain: first pass

First computed pass of the centrality and fragmentation measures proposed in
[research-proposal.md](../research-proposal.md) (network-measures section).
All figures 2024 CHK basis unless dated; compute-code rows use the monthly panel
(through 2026-04); upstream/chips rows use the Atlas HS2012 annual data.
Generated in-session; a scripted module (roadmap step 1) will reproduce these.

## Centrality (2024)

Whole chain (all stages combined):

| measure | #1 | #2 | #3 | #4 |
|---|---|---|---|---|
| HITS hub (export) | TWN 0.26 | KOR 0.17 | SGP 0.11 | MYS 0.08 |
| HITS authority (import) | CHK 0.39 | USA 0.15 | SGP 0.07 | TWN 0.06 |
| PageRank | CHK 0.14 | TWN 0.14 | USA 0.09 | KOR 0.08 |
| conduit min(in,out) | CHK $203B | USA $132B | TWN $109B | SGP $86B |

Selected per-stage: equipment hubs JPN 0.24 / NLD 0.15 / USA 0.10, equipment
authority CHK 0.35 (the build-out); chips hubs TWN 0.29 / KOR 0.21, chips
authority CHK 0.48; servers hub MEX 0.59 (!) vs TWN 0.30, servers authority
USA 0.82 — the strongest single-node dominance anywhere in the data.

**Readings.** (i) Value-weighted whole-chain HITS crowns Taiwan — the formal hub
of the network, not just the narrative's. (ii) The two monopsonies sit at
different layers: China absorbs the middle of the chain (chips authority 0.48),
the US absorbs its end (servers authority 0.82). (iii) The predicted failure
modes materialize exactly: stage-local centrality crowns Mexico (servers hub
0.59 — the Mexico illusion, formalized), and conduit mass flags Singapore
($86B passing through, never top in hub/authority — the entrepot signature).
(iv) CHK's authority carries a double-counting asterisk: much of it is
chips-for-reexport absorption, which rent-weighted centrality would deflate.

## Concentration and centrality by stage (2024)

| stage | total | HHI exp / imp | top HITS hub | top HITS authority |
|---|---|---|---|---|
| raw materials | $13B | 0.10 / 0.07 | USA 0.25 | **CHK 0.19** |
| wafers | $25B | **0.17** / 0.11 | JPN 0.44 | **CHK 0.29** |
| litho/optics | $38B | 0.10 / 0.14 | JPN 0.21 | **CHK 0.38** |
| equipment | $244B | 0.09 / 0.10 | JPN 0.24 | **CHK 0.35** |
| chips | $823B | 0.12 / 0.17 | TWN 0.29 | **CHK 0.48** |
| parts | $132B | 0.14 / 0.14 | TWN 0.30 | **USA 0.39** |
| baseboards | $73B | **0.38** / 0.18 | **TWN 0.77** | USA 0.43 |
| servers | $117B | 0.16 / 0.21 | MEX 0.59 | **USA 0.82** |

**Reading 1 — the authority handoff.** The top authority is CHK for every stage
from raw materials through chips, then flips to USA for every stage after. The
chain's direction of pull, read straight down one column: the world's inputs
drain into China (the production pole), the world's outputs drain into the US
(the consumption pole), and the handoff happens exactly at the parts stage —
where fabrication ends and systems begin.

**Reading 2 — baseboards is the outlier row, and it is the bottleneck.** Export
HHI 0.38 and a hub score of 0.77 (Taiwan) — two to four times any other stage on
both measures — and it is precisely the stage whose unit values rose 20x. Here
the naive measures do flag the true choke point, because Taiwan's packaging
dominance happens to be country-level and within-code. The contrast pair remains
wafers (second-highest exporter HHI 0.17, JPN hub 0.44, prices flat — slack
demand) and servers (MEX hub 0.59 but exporter HHI only 0.16 — bilateral
dominance of a globally diversified stage). Concentration flags candidates;
the price test convicts or acquits.

## Fragmentation over time (compute codes, monthly panel)

Blocs: US-aligned = USA/CAN/MEX/JPN/KOR/TWN/AUS/ISR/Europe; China = CHK;
rest = nonaligned/connectors.

| share of world trade | 2020 | 2022 | 2023 | 2024 | 2025 | 2026* |
|---|---|---|---|---|---|---|
| US-bloc <-> China direct | 31.7% | 29.7% | 25.0% | 21.8% | 13.1% | 10.5% |
| within US-bloc | 46.6% | 46.3% | 50.0% | 50.5% | 58.6% | 58.0% |
| US-bloc <-> nonaligned | 9.2% | 10.5% | 11.8% | 15.0% | 18.2% | 22.6% |
| modularity vs blocs | ~0 | 0.007 | 0.016 | 0.016 | 0.026 | 0.015 |

*2026 = Jan–Apr.

**Readings.** (i) **Exclusion from growth, not decoupling of levels**: direct
US-bloc↔China trade is ~flat in dollars (~$74B 2020, ~$78B 2024, ~$82B 2025)
while the network tripled — China's share collapsed because the boom happened
without it, not because flows were cut. (ii) **Friend-shoring in real time**:
the AI build-out was sourced inside the aligned bloc (within-US share 47→59%).
(iii) **The connectors connected toward the US side**: nonaligned trade share
with the US bloc rose 9→23% while its share with China fell.

## The stage-position gradient (the headline finding)

| stage group | US<->CN direct | trend | within-US | modularity |
|---|---|---|---|---|
| upstream (materials/wafers/optics/equip) | ~25% | flat 2018–2024 | 43–50% | ≈ 0 |
| midstream (chips) | 34.5% → 29.6% | mild decline post-2022 | ~19% | −0.06, stable |
| downstream (compute goods) | 32% → 10.5% | collapse, accelerating 2025 | 47% → 59% | positive, rising |

**The chain fragments top-down.** Finished goods aligned with geopolitics first
and hardest; the chips layer remains the network's great cross-bloc integrator
(its biggest corridors — TWN→CHK, KOR→CHK — span the divide by construction);
the upstream tool-and-materials trade shows no fragmentation at all, because the
dependency is mutual — China must buy, the toolmakers want to sell. The EUV ban
is value-invisible at this aggregation (DUV/legacy dominate dollars): controls
bite below the HS6 level. The midstream integration is exactly what China's fab
build-out — visible upstream as its rising equipment import share — is racing to
internalize; if it succeeds, the chips layer's integration is the next to go.

## Caveats

Bloc assignment does real work (TWN/KOR as US-aligned is defensible but decisive
for within-bloc numbers — robustness to reassignment needed); 2026 is partial;
gross flows double-count (CHK authority inflated); sub-HS6 blindness hides the
narrow chokepoints (EUV, HBM); all numbers pre-date the scripted module and
should be regenerated by it.
