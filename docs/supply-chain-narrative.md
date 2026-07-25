# The AI-compute supply chain, 2017–2026: what moved, and what the trade data shows

An anecdotal but number-anchored account of how the hardware supply chain behind AI
data centers evolved, told alongside our own monthly panel (HS 847150 servers,
847180 baseboards, 847330 parts/cards; panel construction and validation:
[data.md §3](data.md)). Dollar figures are from the audited panel (2017-01+,
Growth Lab reconciliation) unless noted; industry events from the public record.
Model claims are from the TV-MFM re-estimated on that panel. Written 2026-07.

## The chain itself: stages, products, sizes, places

Before the story, the map. The stage definitions and HS6 code lists come from the
OECD's *Mapping the semiconductor value chain* (2025, doi:10.1787/4154cdbf-en) and
the Fed's AI-compute basket (FEDS Note, 2026-02-13), as pinned down in
[data.md §1](data.md); the dollar sizes and corridors are from
our own bilateral data (2024, HS2012 files; the three panel codes also from the
monthly panel). The whole traded chain was ~$1.66T in 2024, more than half of it
the chips stage.

| # | stage | key HS6 codes | 2024 trade | who exports → who imports |
|---|---|---|---|---|
| 1 | Raw materials: polysilicon, rare gases, gallium/germanium, specialty chemicals | 280461, 280421/29, 282560, 811292/99 | part of ~$143B (stages 1–2 + optics inputs) | China (Ga/Ge ~90%/60%, polysilicon), Germany/US (polysilicon), Japan (gases, photoresists) → fab countries |
| 2 | Wafers and wafer inputs | 381800 (doped wafers), 3701xx/370790 (photo plates & chemicals) | — (in the $143B above) | Japan (Shin-Etsu, SUMCO — half the world's wafers), Taiwan, Germany, Korea → Taiwan/Korea fabs |
| 3 | Fab equipment & lithography optics | 8486xx, 9001xx/9002xx, 901210/90, 903141, 903082/84 | **$249B** | Japan 14%, US 13%, Netherlands 10% (ASML), Germany 8% → **China 23%** (Japan→China $16B, NL→China $9B), Taiwan, Korea |
| 4 | Chips: logic, memory (incl. HBM), discretes, IC parts | 854231/32/33/39/90, 8541xx, 852351/52/59 | **$926B — 56% of the chain** | Taiwan 19%, China 17%, Korea 14% (memory/HBM), Singapore 10%, Malaysia 9% (packaging/test) → the China sphere absorbs 43% (China→HK $72B, Taiwan→China $52B, Korea→China $45B) |
| 5 | Parts, boards, GPU cards/modules | **847330** (+ bare PCBs 853400) | $146B | China-led in tonnage; the high-value AI slice from Taiwan (CoWoS-packaged modules) → US, Mexico, everywhere |
| 6 | Baseboards / subassemblies (HGX trays) | **847180** | $101B | Taiwan dominant → US, Mexico |
| 7 | Finished AI servers | **847150** | $127B (→$262B in 2025) | Mexico and Taiwan → the US, which absorbs ~34% of world imports of the compute codes (42% by 2025) |
| 8 | The rest of the data center: switches, optics, power, storage | 851762/851770, 854470/900110, 850440, 847170, 853400 | ~$450B (Tier B basket) | China, Mexico, Malaysia, Thailand → US and everywhere |

The same map as flow charts (`exports/`, regenerate with
`python scripts/export_supply_chain_sankey.py`): a multi-column overview of all
eight stages in two scale versions (dollar and normalized; a log version was
tried and retired — it wholesale-inflates small, Other-dominated stages), a
country-network graph (nodes = countries, edges = flows by stage — the view
that shows an integrated assembler like Mexico correctly: chips and parts in,
servers out at one node), plus one four-column chart per stage
routing the flows through factor-model hubs (exporters -> export hubs -> import
hubs -> importers). The default figures below use the NONNEGATIVITY-IDENTIFIED
basis — the unique admissible bundle basis (see modeling-brainstorm.md §III.4),
so the hub decomposition is an identified object, not a rotation convention;
varimax and unrotated spectral variants live in exports/ for comparison. Hub
decompositions fit at R^2 0.95-0.99, so these carry the flows faithfully.

![network](https://raw.githubusercontent.com/jasonzhixinglu/global-export-complexity/main/exports/network/supply_chain_network_2024.png)
![overview dollar coarse](https://raw.githubusercontent.com/jasonzhixinglu/global-export-complexity/main/exports/overviews/supply_chain_overview_dollar_coarse_2024.png)
![overview dollar](https://raw.githubusercontent.com/jasonzhixinglu/global-export-complexity/main/exports/overviews/supply_chain_overview_dollar_2024.png)
![overview normalized](https://raw.githubusercontent.com/jasonzhixinglu/global-export-complexity/main/exports/overviews/supply_chain_overview_normalized_2024.png)
![overview normalized coarse](https://raw.githubusercontent.com/jasonzhixinglu/global-export-complexity/main/exports/overviews/supply_chain_overview_normalized_coarse_2024.png)
![raw materials](https://raw.githubusercontent.com/jasonzhixinglu/global-export-complexity/main/exports/hubs_nnf/supply_chain_1_raw_materials_nnf_hubs_2024.png)
![wafers](https://raw.githubusercontent.com/jasonzhixinglu/global-export-complexity/main/exports/hubs_nnf/supply_chain_2_wafers_nnf_hubs_2024.png)
![litho optics](https://raw.githubusercontent.com/jasonzhixinglu/global-export-complexity/main/exports/hubs_nnf/supply_chain_3_litho_optics_nnf_hubs_2024.png)
![equipment](https://raw.githubusercontent.com/jasonzhixinglu/global-export-complexity/main/exports/hubs_nnf/supply_chain_4_equipment_nnf_hubs_2024.png)
![chips](https://raw.githubusercontent.com/jasonzhixinglu/global-export-complexity/main/exports/hubs_nnf/supply_chain_5_chips_nnf_hubs_2024.png)
![parts](https://raw.githubusercontent.com/jasonzhixinglu/global-export-complexity/main/exports/hubs_nnf/supply_chain_6_parts_nnf_hubs_2024.png)
![baseboards](https://raw.githubusercontent.com/jasonzhixinglu/global-export-complexity/main/exports/hubs_nnf/supply_chain_7_baseboards_nnf_hubs_2024.png)
![servers](https://raw.githubusercontent.com/jasonzhixinglu/global-export-complexity/main/exports/hubs_nnf/supply_chain_8_servers_nnf_hubs_2024.png)

All charts merge China+Hong Kong (CHK; intra-bloc flows excluded) and show 2024,
the latest year covered by every stage. Stages 1-5 are Atlas HS2012 annual
bilateral data; stages 6-8 the Comtrade+TDM monthly panel. In the overview,
parts+baseboards form a single intra-assembly gap (trade among assembly
countries), because in-country transformation is invisible to customs data —
Mexico imports chips and parts and exports finished servers, performing the
intermediate stages domestically.

Two facts about this map shape everything downstream. First, **each stage lives in
different countries**, so the chain *is* a sequence of border crossings: Japanese
wafers and Dutch machines into Taiwanese fabs; Taiwanese chips into Korean-memory-
laden modules; modules into Mexican assembly; servers into US data centers — with
design value (Nvidia, USA) never appearing in goods trade at all. (The firm-level
anatomy behind these country corridors — which companies each edge stands for —
is mapped in [notes/firm-level-supply-chain-data.md](notes/firm-level-supply-chain-data.md).)
Second, the monthly panel now covers **all eight stages from 2017**, though this
narrative reads mainly the final segment (stages 5–7), where the AI reorganization
happened; the chips-stage story is the natural sequel.

## The starting point: a PC-era network (2017–2021)

Before the boom, these three product codes described the personal-computer and
ordinary-server industry. The network had a settled shape: China made and shipped
parts (~25% of world exports in these codes in 2020, ~$31B of it in 847330 by its
own report — partner mirrors say up to ~$46B), Hong Kong churned re-exports both
directions, Taiwan supplied components (a 10% share — respectable, unremarkable),
and Mexico assembled ordinary servers for the US market (~$20B/yr northbound).
The 2018–19 tariff war bent flows (the cross-bloc channel share of trade stepped
down by a third in 2019 and never recovered) but at the country level the
network's *shape* held. 2021 was a big year for the *old* network: pandemic PC
demand, the crypto-mining GPU boom, and shortage-driven double-ordering pushed
totals to ~$250B. The stress of 2021 was logistics — chip shortages, port
congestion — not structure.

## 2022: pressure without transformation (at the surface)

Three things happened that would matter later: the Shanghai lockdowns (spring)
rattled electronics assembly and accelerated "China+1" plans; the US CHIPS Act
passed (August); and on October 7 the US imposed its first sweeping export
controls on advanced chips to China. Meanwhile the PC boom deflated and crypto
mining died (Ethereum's September merge). Totals plateaued (~$270B) and the
country-level factor model stays calm through the year. But the strictest model
configuration — both China+HKG and USA+MEX merged into blocs, which nets out
intra-bloc churn and isolates cross-bloc structure — **dates an era break at
exactly October 2022**, the month the controls landed; the CHK-merged parts
network breaks the same month. The controls did reorganize the cross-bloc wiring
from day one; it just wasn't visible until the bloc lens was applied.

## 2023: the pivot year — smaller totals, different contents

The strangest year in the data. Total trade in these codes *fell* (to ~$254B;
847330 dropped from $142B to $113B) because the PC slump was still deflating the
old network. But underneath, the composition flipped:

- **November 2022**: ChatGPT. **May 24, 2023**: Nvidia's earnings guidance ~50%
  above expectations — the moment AI demand became hardware orders.
- **July 2023**: the orders became shipments. H100 modules and HGX baseboards began
  leaving Taiwan in volume; TSMC used its July earnings call to announce a doubling
  of CoWoS advanced-packaging capacity; by September its chairman called CoWoS "the
  shortage." The factor model dates its single dominant break to **2023-08** —
  the first estimation month fully carrying those shipments. Before it: one
  unbroken 68-month era back to 2017. Taiwan's export behavior separates from the
  rest of Asia at this break.
- The same month, China restricted gallium/germanium exports (July 3), and in
  October the US banned the China-market H800/A800 chips.

The clearest fingerprint is not value but *price*: Taiwan's baseboard exports
(847180) jumped from ~$285/kg in 2022 to ~$1,500/kg in 2023 — same kind of boxes,
five times the value per kilogram. AI hardware was replacing PC hardware inside the
same customs categories. Taiwan's world export share jumped from 12.4% to 20.2% in
a single year while China's slid from 23.4% to 20.5%.

## 2024: scale-up

The first full year of the AI-hardware economy: totals up ~47% to $374B, led by
servers (847150: $85B → $127B) and baseboards ($56B → $101B). Blackwell was
announced in March and ramped late in the year through the same packaging
bottleneck. The corridor build-out is visible line by line:

- Taiwan → USA more than doubled ($26B → $56B).
- Taiwan → Mexico nearly tripled ($1.7B → $4.8B): baseboards feeding Mexican final
  assembly, which sent $29B of finished hardware north.
- China's *direct* exports to the US stayed flat (~$6B) — its share of world
  exports fell to 16.4% while Taiwan's reached 26.0%. The two lines crossed.
- **October 2024**: the CHK-bloc model breaks era — the China-bloc export hub
  loses its separate identity (cross-era similarity drops to 0.45, against
  0.9+ for every other hub) and a **Singapore-led export factor is born**,
  serving the Taiwan import hub. This is the quarter HBM controls were signaled
  and pre-positioning began; December brought the controls themselves plus
  China's retaliatory hard ban on gallium/germanium to the US.

## 2025: the policy year — and the blow-off in values

Totals up another ~82% to $682B. Every corridor in the AI chain exploded: Taiwan →
USA hit $136B (18x its 2020 level), Taiwan → Mexico $16B (3x in one year), Mexico →
USA $75B, parts southbound USA → Mexico $25B. And the tariff shock arrived:

- **April 2025**: the tariff announcement (April 2, electronics partially
  exempted days later amid confusion) plus the H20 export ban. In the strictest
  double-bloc configuration this is an era break, and its anatomy is distinctive:
  the China-bloc and US-bloc export patterns became **entangled** — they load
  together on a single factor (CHK +3.97, USM +3.41), the signature of a common
  policy shock hitting both blocs at once. Nothing comparable happens at any
  other break. The Singapore factor (born 2024-10) persists and strengthens; the
  raw corridor concurs: Singapore → USA, ~$1B or below for years, hit $4.5B in
  2025 amid public smuggling crackdowns and rerouting scrutiny of Singapore and
  Malaysia. (The H20 was partially re-allowed mid-year under a revenue-sharing
  arrangement.)
- Onshoring became real money: TSMC's Arizona commitment grew toward $265B; server
  assembly plants opened in Texas. Late in the year, rack-scale systems (NVL72)
  began changing what physically crosses borders at all.
- Taiwan's share of world exports in these codes reached **30.4% — beyond the
  ~25% China held in 2020, with China down to 10.7%**. A five-year swap of the
  two poles of the network.

## 2026 so far: still accelerating

January–April alone: $371B across the codes (~$1.1T annualized). Taiwan's exports
to the US are running at ~$190B/yr pace; its overall trade surplus with the US
topped $100B in a half-year for the first time, feeding tariff tension. Unit
values keep climbing (Taiwan baseboards near $5,900/kg — 20x 2022). Hong Kong
remains the China bloc's conduit — its re-exports into China hit $50B in 2025 —
but everything it does nets out inside the CHK bloc. China's direct shipments to
the US in these codes remain a rounding error (~$6–11B/yr against a $680B
market). The country-level model opened a fresh era in mid-2025 that is still
running: the hubs have *purified* (each hub now nearly one country: Taiwan alone,
Mexico+Korea, Singapore, USA) — the network is more concentrated and more
bloc-sorted than at any point in the sample.

## The shift in one table

Share of world exports, all three codes (audited panel):

| exporter | 2020 | 2023 | 2025 | direction |
|---|---|---|---|---|
| China | 24.8% | 20.5% | 10.7% | halved — the old parts hegemon |
| Taiwan | 10.0% | 20.2% | 30.4% | tripled — the new pole |
| Mexico | 10.3% | 9.6% | 12.4% | steady conduit, bigger pipe |
| Hong Kong | 9.4% | 8.1% | 9.8% | share steady — but purely intra-bloc conduit work, netted inside CHK |
| Vietnam | 1.8% | 4.9% | 3.5% | tripled to 2023, partial retreat since |
| Singapore | 2.7% | 2.4% | 5.7% | flat, then the 2025 jump |

## Value vs volume: mostly a price story

Taiwan's export unit values ($/kg, TDM customs data):

| code | 2020 | 2022 | 2023 | 2025 | 2026 |
|---|---|---|---|---|---|
| 847150 servers | 262 | 360 | 765 | 1,678 | 1,849 |
| 847180 baseboards | 111 | 285 | 1,514 | 3,646 | 5,877 |
| 847330 parts | 171 | 204 | 195 | 280 | 242 |

The dollar explosion is overwhelmingly about what is *inside* the boxes, not how
many boxes. Baseboard value-per-kilogram rose ~20x from 2022 to 2026; parts stayed
almost flat until 2025 (generic PC components still dominate that code's tonnage).
Any volume-based reading of this trade (weight, containers) misses most of the
story; any value-based reading overstates physical reorganization.

## What policy did — the revised reading

On the audited 2017+ panel the model's verdict on policy is sharper, and different
in one important way from our earlier account (which was estimated on a shorter,
pre-audit panel and understated the controls).

**Where you look determines what policy you can see.** At the country level, the
only dominant break in nine years is the demand event (2023-08); policy events
barely register because their effects are rerouting *between* bloc members. But
in the strictest configuration — CHK and USA+MEX both merged, so intra-bloc churn
cancels — **every major policy regime start leaves a break**: the 2018–19 tariff
war (breaks at 2019-04 and 2019-12), the first export controls (a break at
exactly **2022-10**, also visible in CHK-merged parts), and the 2025 tariffs
(**2025-04**, the entanglement break). Demand breaks countries; policy breaks
blocs.

**What the controls did to levels** (beyond the 2022-10 wiring break): they
*denied China the boom*. China-bloc imports of these codes grew only modestly in
ordinary dollars ($23B in 2023 to $35B in 2025 — compliant chips and ordinary
components) while its share of world imports fell from ~10% (2022) to 5.2%
(2025), and the US share climbed to 42.5%. The US bought five times more in 2025
than in 2020; China's bloc barely moved. The controls also left routing
fingerprints — Taiwan-to-China-bloc nearly doubled in 2024 ($5.5B → $10.4B, the
compliant-variant module trade); Hong Kong re-exports into China reached $50B in
2025 — but the bloc-merged model nets these out: routes moved within the wall.
The late-2024 HBM round is the one control event with a structural echo of its
own — the 2024-10 era break where the China-bloc hub dissolves and the Singapore
factor appears. One caveat stands: the controls' real battlefield is bare chips
(HS 8542.31), and the chips-stage panel now exists to test exactly that.

**What the tariffs did**: the 2025-04 break is the only one where the two blocs'
export patterns *entangle* on a common factor — a policy shock hitting both
sides simultaneously — and it did not cut volumes; exemptions kept the Taiwan and
Mexico corridors booming. Tariffs changed which routes exist and who co-moves,
not how much flows.

The general lesson (revised): policy reorganizes the *cross-bloc* wiring, demand
reorganizes the *country* structure — and a factor model sees each only at the
aggregation level where the other is netted away.

## How to read all of this (the standing caveats)

Gross shipments still double-count the chain (a Taiwan board is re-counted inside a
Mexican server), re-exports still inflate entrepots, and the biggest value slice —
US chip design — never appears in goods trade at all. The Mexico-vs-Taiwan contrast
runs through every year above: Mexico's numbers grew because more value passes
*through* it; Taiwan's grew because more value is *created* there. See
docs/modeling-brainstorm.md for what we intend to do about that distinction.
Panel construction, validation against Atlas, and the audit that corrected the
earlier estimation: [data.md §3](data.md).
