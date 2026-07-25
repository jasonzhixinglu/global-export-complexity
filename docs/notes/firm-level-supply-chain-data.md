# Firm-level supply-chain data: what the H200-Sankey ecosystem uses, and what it's worth to us

Prompted by the flow chart in the thumbnail of the YouTube video "The Insane
Complexity of the Semiconductor Global Supply Chain" (channel: Micro,
[video](https://www.youtube.com/watch?v=Gj5liYnpTeM)). That chart is the
whole-industry variant of a visualization that circulated as a Reddit
r/dataisbeautiful original: **"[OC] The supply chain of an Nvidia H200 chip"**
(D3-Sankey + React; creator's handle not recovered — the mirror site blocks
fetches; the video description or a Reddit search for the title should give it).
Covered by [PC Gamer](https://www.pcgamer.com/hardware/graphics-cards/this-supply-chain-sankey-diagram-for-an-nvidia-ai-megachip-is-a-handy-guide-to-understanding-just-how-easy-it-is-to-ruin-the-prices-of-graphics-cards/);
[mirror of the post](https://www.usluck.com/843021/the-supply-chain-of-an-nvidia-h200-chip-oc/).

## 1. What the visualization actually shows

A firm-level Sankey of the semiconductor chain, three tiers deep:

- **Tier 3 sub-suppliers → Tier 1 equipment**: Zeiss SMT (EUV optics, sole
  supplier) and Trumpf (EUV drive lasers, sole supplier) and Cymer (light
  sources, ASML-owned) into **ASML**; VAT (vacuum valves), Pfeiffer (vacuum),
  MKS Instruments, TOTO (electrostatic chucks) into the deposition/etch makers.
- **Materials**: Shin-Etsu, SUMCO (wafers); JSR, TOK (photoresists); Entegris
  (handling/filtration); Air Liquide / Linde (gases).
- **Tier 1 → fabs/memory**: ASML, Applied Materials, Lam, KLA, Tokyo Electron
  into **TSMC**, Samsung, **SK Hynix**, Micron.
- **Fabs → designers**: TSMC/memory makers into Nvidia (labeled $130B ≈ FY2025
  revenue), Apple, AMD, Broadcom, Qualcomm, MediaTek. **EDA/IP (Synopsys,
  Cadence, Arm) flow directly to designers** — consumed at design time, not
  through fabs. Link widths are spend-per-chip (H200 version) or revenue
  (industry version); each node's inflows are normalized to equal outflows.

Headline claims of the H200 version worth remembering: SK Hynix's and TSMC's
flows into the H200 are nearly equal — **HBM3e costs roughly as much per H200
as the GPU die itself**, making HBM supply, not logic capacity, the production
bottleneck.

## 2. Their data sources, one by one

| source | what it is | what they took from it | access |
|---|---|---|---|
| SEC 10-K filings (Nvidia, TSMC, ASML, AMAT, Lam...) | audited annual reports; revenue, segment splits, named customers >10% of revenue, supply commitments | company revenues (node sizes); some customer-concentration edges | free (EDGAR) |
| SemiAnalysis | industry research shop (Dylan Patel); teardown-grade bill-of-materials estimates | the **H200 BOM breakdown** — dollar cost per component per chip (the per-chip link widths) | newsletter partly free, BOM detail paywalled; their own podcast/essay on the shortage: [The Great AI Silicon Shortage](https://newsletter.semianalysis.com/p/the-great-ai-silicon-shortage) (not the chart's author — a source it drew on) |
| TrendForce | Taiwanese market-research firm; quarterly memory/foundry trackers | **HBM market shares** (SK Hynix / Samsung / Micron split) | press releases free, reports paid |
| SEMI | industry association | equipment market data (billings by segment/region — sizes the equipment tier) | headline series free, detail member-paid |
| Yole Group | French tech market research | advanced packaging / **substrate** market analyses (the CoWoS/substrate nodes) | press summaries free, reports paid |
| Veridion | commercial supplier-relationship graph (web-scraped + curated firm-to-firm edges) | the **edge list** — who supplies whom | commercial API |

Method in one line: take firm revenues (10-K) as node masses, connect nodes
with relationship data (Veridion, 10-K customer disclosures), and weight edges
with BOM/market-share estimates (SemiAnalysis, TrendForce, Yole, SEMI).

## 3. How this differs from what we build

| | their chart | our panel/model |
|---|---|---|
| unit | firm | country (30 + ROW) |
| flow measure | revenue / estimated spend per chip | customs-recorded trade values |
| time | snapshot (one fiscal year / one chip generation) | monthly, 2017-01 → present |
| coverage | one product's chain (H200) or named large firms | all trade in 60 HS6 codes, all reporters |
| identification | assembled by hand from disclosures + estimates | measured flows + factor model |
| can see | WHO exactly supplies whom; monopoly structure; within-country value splits | reorganization over time: breaks, rerouting, repricing, substitution |
| cannot see | dynamics, substitution under stress, anything private firms don't disclose | firms; domestic (in-country) stages; within-HS6 product mix |

The two are complements: theirs is the corporate anatomy, ours is the measured
circulation.

## 4. Concrete uses for us (ranked)

1. **External check on the stage taxonomy (cheap, do first).** Every firm in
   their chart should map into exactly one of our stages 1–8 via its main
   product, and its country into that stage's expected exporters. Zeiss SMT →
   stage 3 / DEU; Trumpf → stage 3 / DEU; ASML → stage 4 / NLD; Shin-Etsu,
   SUMCO → stage 2 / JPN; JSR/TOK → stage 2 / JPN; Entegris → stage 1-2 / USA;
   SK Hynix/Samsung → stage 5 / KOR; TSMC → stage 5 / TWN. Any firm we cannot
   place (e.g. TOTO chucks, VAT valves — plausibly outside our 60 codes) marks
   a taxonomy hole worth noting. First pass says the map is clean and the holes
   are small-dollar.
2. **Validate country shares within stages.** Their firm market shares imply
   country export shares in our data: wafers (Shin-Etsu + SUMCO ≈ dominant) →
   JPN should dominate 381800 exports; EUV (ASML 100%) → NLD should dominate
   the litho slice of 8486; HBM (TrendForce splits, SK Hynix-led) → KOR should
   dominate 854232 exports to TWN. These are direct, quantitative cross-checks
   of our stage charts — agreement validates both the taxonomy and the pull.
3. **Test the HBM-bottleneck claim in our panel.** If HBM ≈ GPU die per unit,
   the KOR→TWN memory flow (854232) should be comparable in dollars to the
   value TSMC adds per accelerator — checkable against our KOR→TWN series and
   Taiwan's unit-value data. Their BOM gives us an external anchor for the
   within-847180/847330 composition we cannot see in customs data.
4. **Sharpen the concentration-vs-power interpretation.** Their monopoly list
   (Zeiss 100% EUV optics, Trumpf 100% drive lasers, ASML 100% EUV) tells us
   where country-level HHI *understates* power: NLD's equipment exports look
   diversified across partners, but the firm layer is a monopoly. This is a
   ready-made appendix argument for why our power metric (counterparty origin
   concentration) needs the firm layer as a lower bound.
5. **Layer-2 input (future).** Veridion-style firm-edge data is the commercial
   version of what our roadmap calls chain accounting. Not worth buying now;
   worth knowing it exists if the project needs firm resolution later.
6. **Source shopping list.** TrendForce HBM shares (free PRs) and SEMI billings
   (free headline series) are usable today as external series to correlate
   against our stage-4/5 flows; SemiAnalysis BOM numbers are the only paid item
   with unique content for us.

## 5. The edge-by-edge mapping: their firm flows as our country x HS6 flows

For each edge family in their Sankey: which countries the goods physically move
between (production sites, not HQs), under which HS6 code, and whether our
60-code panel can see it.

| their edge | firms | physical flow (exporter → importer) | HS6 | in our 60? | notes |
|---|---|---|---|---|---|
| EUV/DUV optics → ASML | Zeiss SMT | DEU → NLD | 900190/900290 (optical elements) | **yes** (stage 3) | clean, testable: DEU should dominate NLD's optics imports |
| EUV drive laser → source | Trumpf | DEU → USA (Cymer, San Diego) / NLD | 901320 lasers | **no** | taxonomy hole: laser sources outside basket |
| light source → ASML | Cymer (ASML-owned) | USA → NLD | 848690 (litho parts) | **yes** (stage 4) | shows inside the parts-for-8486 flow |
| vacuum valves/pumps → equipment makers | VAT, Pfeiffer | CHE/DEU → USA/JPN/NLD | 848180 valves, 841410 pumps | **no** | deliberately excluded generic codes; small $ |
| chucks, gauges, RF → equipment makers | TOTO, MKS | JPN/USA → equipment sites | mixed (8486 parts, 9026/9032) | partial | mostly inside 848690/903082 if at all |
| wafers → fabs | Shin-Etsu, SUMCO | JPN → TWN/KOR/CHN/USA | **381800** | **yes** (stage 2) | flagship check: JPN should dominate world 381800 exports and TWN/KOR imports |
| polysilicon → wafer makers | Hemlock, Wacker, Tokuyama | USA/DEU/JPN → JPN/TWN/KOR | **280461** | **yes** (stage 1) | clean |
| photoresists → fabs | JSR, TOK, Shin-Etsu | JPN → TWN/KOR/CHN | 370790 (+3701 masks) | **yes** (stage 2) | JPN dominance is the OECD-documented >90% chokepoint |
| specialty gases → fabs | Air Liquide, Linde | (mostly on-site/domestic) | 280421/29 | partial | **largely invisible by construction**: bulk gases are produced next to the fab, not traded; only specialty molecules cross borders |
| handling/filtration → fabs | Entegris | USA/SGP/TWN plants → fabs | 8421xx + plastics | partial | production is multi-country; weak mapping |
| litho/dep/etch tools → fabs | ASML, AMAT, Lam, TEL | NLD/USA/SGP/JPN → TWN/KOR/CHN/USA/IRL/ISR | **848620** (+848690) | **yes** (stage 4) | the biggest equipment edge; NLD→TWN is EUV almost by definition |
| metrology/inspection → fabs | KLA, Advantest | USA/JPN/SGP → TWN/KOR/CHN | 903082/903141 | **yes** (stage 4) | |
| EDA/IP → designers | Synopsys, Cadence, Arm | — | — | **no, structurally** | services/licenses, not goods; **never in customs data**. Their chart routes these straight to designers for the same reason |
| HBM → CoWoS packaging | SK Hynix, Samsung | KOR → TWN | **854232** | **yes** (stage 5) | THE testable bottleneck edge; TrendForce shares give the KOR split |
| HBM (Micron) → CoWoS | Micron | fabs in TWN/JPN/SGP → TWN | 854232 | partial | Micron's TWN-made HBM → TSMC is **domestic, invisible**; only its JPN/SGP output crosses a border |
| ABF substrates → packaging | Ibiden, Shinko, Unimicron | JPN/TWN → TWN | 853400 | **no** (Tier B) | known Tier-B extension code |
| "TSMC → Nvidia" | TSMC, OSATs, ODMs | **not a country edge**: materializes as TWN exports of chips/modules/boards (8542xx, 847330, 847180) to assembly countries (CHN/MEX/USA/VNM), then servers (847150) onward | multiple | **yes** | the single most important translation: designer revenue edges appear in customs as TWN→assembly→datacenter chains, which is exactly the structure our stage charts show |

Four structural reasons a firm edge can be invisible in ANY customs data —
worth keeping in mind when the two pictures disagree:

1. **Services, not goods** (EDA, IP, design royalties — Synopsys/Cadence/Arm).
2. **Domestic co-location** (gases made on-site; Micron's Taiwan HBM feeding
   TSMC; everything both firms do inside one country).
3. **Codes outside the basket** (lasers 901320, valves/pumps, ABF substrates
   853400 — each small or Tier-B).
4. **Ownership ≠ geography** (Cymer is ASML-owned but ships USA→NLD; a
   "purchase" by Nvidia is physically a TWN→MEX module shipment).

The mapping also works in reverse and that is its real value: each of our
stage-level country corridors now has a named-firm interpretation (NLD→TWN
848620 ≈ ASML→TSMC; KOR→TWN 854232 ≈ SK Hynix HBM→CoWoS; JPN→TWN 381800 ≈
Shin-Etsu/SUMCO→TSMC; DEU→NLD 900290 ≈ Zeiss→ASML), which upgrades our charts
from anonymous country flows to a checkable corporate story.

## 6. Caveats

- The chart's numbers mix audited revenue with estimates (BOM allocations,
  market shares); its per-chip flows are modeling, not measurement — treat as
  priors, not ground truth.
- Firm HQ country ≠ production country (Micron's HBM is made in TWN/JPN/SGP;
  Samsung memory partly in CHN). When we map firms to our country flows, use
  fab locations, not HQs, or the check will produce false alarms.
- Their normalization (node inflow = outflow) is a visual convention; it does
  not conserve value economically the way customs data does.
