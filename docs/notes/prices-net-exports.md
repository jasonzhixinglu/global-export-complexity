# Prices, terms of trade and net exports on the AI-compute chain

First computed pass at three things the value panel could not answer on its own:
**export and import price indices** (country × stage), **terms of trade** and
**net exports** (country, aggregate over the 60-code basket). Monthly, 2017-01
onward. Scripts: `scripts/build_unit_values.py` → `scripts/compute_prices_net_exports.py`;
outputs in `results/tables/` (see the file list at the bottom).

Read the coverage caveat (§5) before quoting any price number. Net exports have
no such caveat — they come straight from the reconciled panel.

## 1. What was computed

**Net exports** (`net_exports.csv`) — from `panel_semi_monthly.parquet`, the same
reconciled flows every other measure uses. For country *c* and month *t*,
exports = all panel flows with exporter *c*, imports = all flows with importer *c*,
over every partner including ROW; `net = exports − imports`. Monthly and 12-month
rolling sums (`*_12m`). Aggregate over all 60 codes, per the ask — not split by stage.

**Price indices** (`price_index_stage_{monthly,roll12}.csv`) — one chained Törnqvist
index per country × flow × stage, built from unit values (USD per kg) in each
reporter's own report:

    dln P_t = Σ_i wbar_it (ln uv_it − ln uv_i,t−1),   wbar_it = ½(s_i,t−1 + s_it)

over the HS6 codes present in both months, *s* being a code's share of the stage's
weight-covered value. Levels of $/kg are meaningless across products, so only the
within-code change is used. Two frequencies: `monthly`, and `roll12` — unit values
from trailing 12-month sums of value and kg, chained monthly. **Read roll12**;
monthly is there for anyone who wants the noise. Each series is 100 at its base
month (2018-01 for all but China, which starts 2018-08, see §5).

**Terms of trade** (`terms_of_trade.csv`) — `tot = 100 × px / pm`, where px and pm
are the same Törnqvist construction run over **all 60 codes at once** (not an
average of stage indices), so it is a country-level number as asked. 100 at base,
so it reads as "since 2018".

Every price file also carries a drift-free companion, `index_direct` /
`tot_direct`: a single Törnqvist comparison of each month against the base month
rather than a chain. A chained index drifts when weights and unit values move
together; where the two disagree, neither is safe to lean on. They agree within 10%
for 10 of the 19 well-covered countries and within 15% for 13; the largest gaps are
NLD (43%), HUN (33%), ESP (25%), IDN (24%), TWN and THA (19%).

## 2. Net exports — the measured picture

12-month totals to 2026-04 (the panel's balanced endpoint), $B:

| net exporters | net | net importers | net |
|---|---|---|---|
| TWN | **+272** | USA | **−264** |
| KOR | +161 | CHN | −242 |
| MYS | +86 | VNM | −78 |
| SGP | +78 | IND | −40 |
| JPN | +42 | THA | −20 |
| HKG | +40 | IDN | −12 |
| PHL | +17 | CAN, POL | −8 each |
| DEU | +16 | GBR | −6 |
| MEX | +14 | BEL | −6 |

Change since the 12 months to 2020-04:

- Taiwan +$192B, Hong Kong +$126B (from −86 to +40), Korea +$105B, Singapore +$52B,
  Malaysia +$48B, Mexico +$20B.
- United States −$264B (from balance to a quarter-trillion deficit on this basket
  alone), China −$128B, Vietnam −$61B, India −$27B, Thailand −$17B,
  Netherlands −$13B (from +10 to −3).

**Interpretation, not measurement:** the two big deficits are different animals.
The US one is the AI build-out landing as finished-hardware imports; China's is
chips flowing in against equipment it increasingly cannot buy. Hong Kong's swing
is entrepôt accounting more than production. None of this is tested here.

## 3. Terms of trade and stage prices — the measured picture

12-month ToT, 2018-01 = 100, countries with usable weight coverage on both flows:

| iso | 2020-06 | 2022-12 | 2024-12 | 2026-06 | direct 2026-06 |
|---|---|---|---|---|---|
| NLD | 106 | 96 | 129 | **153** | 108 |
| TWN | 101 | 115 | 122 | **122** | 103 |
| KOR | 87 | 76 | 90 | **105** | 114 |
| CHN | 94 | 94 | 85 | **99** | 103 |
| DEU | 104 | 108 | 96 | **95** | 100 |
| JPN | 115 | 101 | 98 | **85** | 89 |
| THA | 63 | 18 | 15 | **17** | 14 |

Korea's export price index traces the memory cycle almost exactly: chips exports
121 (2018-12) → 86 (2020-12) → 76 (2023-12) → 129 (2026-04), i.e. the DRAM peak,
the 2023 trough and the current upcycle. That the index reproduces a cycle it was
never told about is the main evidence it is measuring something real.

Stage indices, 2026-06 vs 2018-01 = 100 (12m, coverage ≥ 50%):

| stage | TWN X | KOR X | CHN X | JPN X | NLD X | DEU X |
|---|---|---|---|---|---|---|
| equipment | 179 | 183 | 110 | 117 | **463** | 152 |
| chips | 259 | 133 | 281 | — | 77 | 200 |
| parts (847330) | 213 | **996** | 114 | 141 | 73 | 87 |
| servers (847150) | **643** | 225 | 133 | — | 183 | 225 |

The very large numbers are almost certainly **mix, not price**: a 2026 GPU
baseboard and a 2018 server board share an HS6 code and nothing else. Thailand's
chips *import* index at 1869 is the same effect in its purest form — the basket it
imports changed, not the price of anything.

## 4. Two further cuts: since 2021, and by broad stage

Every index now carries a second base: `*_2021`, the **2021 average = 100** (a
twelve-month average, so the base is not itself a seasonal or one-month accident).
Aggregate terms of trade on that base, 12-month:

| iso | 2021-12 | 2022-12 | 2023-12 | 2024-12 | 2026-06 |
|---|---|---|---|---|---|
| NLD | 97 | 87 | 101 | 126 | **142** |
| KOR | 106 | 98 | 84 | 114 | **133** |
| TWN | 101 | 109 | 126 | 115 | **115** |
| SGP | 96 | 96 | 98 | 109 | **105** |
| MYS | 90 | 102 | 108 | 105 | **100** |
| JPN | 96 | 84 | 88 | 89 | **89** |
| VNM | — | 137 | 125 | 90 | **87** |
| DEU | 98 | 91 | 81 | 81 | **79** |
| CHK | 112 | 105 | 84 | 90 | **72** |
| **USA** | 95 | — | 88 | 82 | **51** |

The US is the sharpest series in the file: its import unit values reach 325 (2021
average = 100) against exports at 170, halving its terms of trade. The stage detail
says where it comes from — servers 571 and baseboards 443 on the import side, against
chips exports at 180. It is paying multiples per unit for finished AI hardware while
selling chips and equipment whose unit values rose far less.

Korea reads far better from 2021 (133) than from 2018 (105): the 2018 base sits at
the top of the memory cycle, so the 2018-based series spends five years climbing
back to where it started.

### Terms of trade of net exports

Eight stages collapse to three — **upstream** (raw materials, wafers, optics, fab
equipment), **chips**, **downstream** (parts, baseboards, servers) — and the ratio
is taken two ways.

*Within a stage* (`terms_of_trade_broad.csv`): a country's export price of that
stage over its import price of the same stage.

*Net position* (`terms_of_trade_net_position.csv`): the broad stages a country is a
net **exporter** of, priced by its exports, over the stages it is a net **importer**
of, priced by its imports. Sides are fixed once over the whole sample so the basket
cannot flip with the data. This is the ratio that answers "is what I sell getting
dearer than what I must buy", and for a processing economy it is the one that
carries information — the within-stage cut mostly cancels, because these countries
buy and sell the same stage.

| iso | sells | buys | net-position ToT (2018) | (2021 avg = 100) | direct |
|---|---|---|---|---|---|
| TWN | chips + downstream | upstream | **226** | 216 | 166 |
| NLD | upstream | chips + downstream | **180** | 140 | 142 |
| VNM | downstream | chips + upstream | **144** | 121 | 107 |
| KOR | chips + downstream | upstream | **127** | 170 | 140 |
| DEU | chips + upstream | downstream | **118** | 97 | 122 |
| JPN | chips + upstream | downstream | **89** | 78 | 90 |
| USA | chips + upstream | downstream | **20** | 32 | 18 |

Taiwan is the clearest result in this note: what it sells has roughly doubled in
unit value against what it buys (226, and 216 of that on the 2021 base), and unlike its
aggregate ToT the chained and direct versions agree in direction. Korea's gain is
recent and almost entirely post-2021. The Netherlands is the mirror image — it
sells the upstream that Taiwan buys.

**Same caveat, sharper.** A net-position ratio compares *different goods* on the two
sides by construction, so it inherits every mix problem in §5 and adds one: the two
baskets have no reason to shift composition at the same rate. Read it as "the value
per kilo of what this country sells, against the value per kilo of what it buys" —
which is a real and interesting quantity — not as a price ratio.

## 5. What this measure cannot do (read before quoting)

**Unit values are not prices.** Dollars per kilo — or per unit — confound price with
quality and with mix inside an HS6 code, and this basket is the worst case for that:
the AI cycle *is* a within-code quality shift. Treat every number above as a unit-value index and say
so; do not call any of it inflation, and do not read a stage index as a margin.

**Coverage is uneven, and thin coverage is disqualifying.** Only the value lines that
carry a usable quantity — weight or units, whichever the reporter measures — can
produce a unit value. Coverage of reported value (`price_coverage.csv`, all-code):

| coverage | countries |
|---|---|
| ≥ 90% both flows | TWN, KOR, JPN, CHN, DEU, NLD, MYS, SGP, ITA, POL, IRL, BEL, DNK, ESP, CHE, GBR, HUN, CZE, SWE, THA, IDN |
| usable | USA (0.68/0.66), VNM (0.73/0.78), HKG, MEX, IND, FRA |
| **too thin to use** | ISR (0.09), PHL (0.41/0.31), CAN exports (0.38) |

Those rows all exist in the CSVs with their `cov_x` / `cov_m` columns — apply your own
bar. The charts use 0.5 on both flows. Net exports are unaffected by any of this.

**The reported weight is often not a measurement.** Several reporters do not weigh,
they derive: net weight = value x a constant, so the implied unit value repeats month
after month. US 847150 imports take **12 distinct values in 113 months**, stepping in
January or mid-year — +10.7% (2018-01), +13.9% (2021-01), −9.1% (2021-12), +5.9%
(2023-12), +4.6% (2025-08) — while value swings from $2.4B to $20.4B a month. Between
steps the price relative is exactly zero, which is not the same as "no price change";
at a step it is an administrative revision dated by the agency's calendar. Both are
excluded (see the detection rule below).

**Two quantities, and the reporter decides which one is real.** Comtrade carries net
weight *and* `qty`, the reporter's own unit. Which one is measured varies by reporter
and code: US weight on the compute codes is derived, but its unit counts are genuine
(~1.5m units of 847150 a month across 50-odd partner lines, $1,610 per unit in 2018-01,
$2,377 in 2023-01, $7,664 in 2025-06); Japan's three biggest chip import codes are the
same story, imputed by weight and clean by unit ($1.50 → $2.20 per IC). So the base
carries both candidates, screens each with the degeneracy test below, and records the
winner per country × flow × code in a `basis` column. Weight keeps its place unless it
is usable in under half the series' months; the choice is made once for the whole
sample, never mid-series, because a chained index tolerates any unit but not a change
of unit.

This lifts usable coverage of basket value from 55% to 89% and puts the US, Japan,
Singapore, Malaysia and Vietnam back on the charts. Only Israel (0.09), the
Philippines (0.31/0.41) and Canada's export side (0.38) now fall below the bar.

A warning from building it: the first version of this looked catastrophic — Japan's
chips import index at 279, Vietnam's terms of trade at 694 — and the cause was not the
data but a stale column name. The builder's output was renamed `quantity` (it is no
longer always kilos) while the index code still divided by `kg`, so every units-basis
series was computing value-with-units over raw weight. The tell was that isolated
rebuilds of the same series came out clean (Japan's chips imports at 119, not 279) while
the pipeline did not. Cross-check kept for the next such change: the countries whose
weights were always sound (TWN, KOR, CHN, DEU, NLD) must come out unchanged when the
quantity logic moves — they did, to the point.

**China and Hong Kong are one series.** `CHK` is built in the base from **extra-bloc
lines only** — China's shipments to Hong Kong are an internal transfer, and a large one
($388B of chips flowed between the two in the year to 2026-04, up from $167B in 2022).
CHN and HKG keep their own all-partner rows alongside it. Two construction notes worth
remembering: summing the two countries would inflate the gross columns by that
entrepôt leg (the net is unaffected), and each member's extra-bloc trade has to keep its
own identity through the Comtrade/TDM source precedence — collapsing to `CHK` before the
merge put two reporters on one key and silently dropped China's TDM leg from 2025,
cutting the bloc's monthly value by three quarters.

**Volatile countries are excluded, not cleaned.** An earlier build screened single
corrupt cells — a month whose unit value sat more than 2.5x from its series' local
median. It worked on the case that motivated it (Malaysia filed 12.4bn units of 854231
in 2025-01 against ~0.5bn either side, with value flat, dragging its 12-month unit value
down 63%) and it halved the volatility of the worst series. It is nonetheless **off**
(`GEC_OUTLIER_LOG`): a rule that drops the awkward months drops the volatile tail
specifically, which biases every surviving index toward calm, and it does so invisibly.

The charts instead exclude a whole country when its terms of trade move more than 3.5%
in a typical month — currently Malaysia (4.4%) and Singapore (6.5%), both re-export
hubs whose basket genuinely churns. The test and the excluded names are printed by the
plot script and stated in the chart caption. This is a display decision, reversible by
one constant, and it leaves the underlying series in the CSVs for anyone who wants them.
For reference the same statistic for the countries that stay: TWN 0.9%, JPN 1.0%,
DEU 1.0%, KOR 2.1%, VNM 2.6%, USA 2.9%, NLD 2.9%, CHK 3.1%.

**Series start where their data does.** A 12-month unit value needs a full window and
the chain needs two adjacent ones, so a country's index begins once its quantities are
usable — not in 2017-01. Most start 2018-01; the China bloc starts **2018-08**, because
China's 2017 weights are all of the imputed kind (42% of value, the series that stepped
~10x at the 2017→2018 revision) and its units column covers only 19% of 2017 value, with
no TDM extract reaching back that far. Hong Kong alone would start 2018-01; the bloc is
as good as its weaker member. A partial-window index would close the gap at the cost of
early points resting on a smaller basket than later ones, which is not worth an
unlabelled discontinuity.

**No churn screen.** An earlier build dropped any code whose unit value moved more than
25% in a median month. It is retained in code but switched off (`SCREEN_CHURN`): it was
motivated by the 3-month charts, which are not published, and at a 12-month window the
averaging already absorbs that noise — while dropping codes leaves the index chaining
over a rump basket, which does its own damage.

**The degeneracy rule.** A series whose unit value takes ≤ max(2, n/2) distinct values
in a year (with at least 6 months observed) is treated as derived rather than measured
and its quantity is dropped — 2.4% of basket value, down from 15.6% before the second
quantity gave most of those series somewhere else to go. Months where a series'
coverage falls below half its own norm, or whose weight-carrying value falls below 40%
of its own median, are dropped as well: the first catches reporting regime changes
(China's entirely-imputed 2017, which is why its series starts 2018-08), the second
catches partial months at the end of the sample.

**Basis.** Exports are FOB, imports CIF, as reported. A constant CIF margin cancels
in a rebased index, so no CIF→FOB step is applied; a *changing* margin (freight
2021-22) does not cancel and would show up as a small ToT decline.

**How much is dropped, in total.** One filter removes observations on quality grounds:
the degeneracy test, at 2.3% of basket value. Everything else is either a choice between
two available quantities (no data lost), a month-level guard against incomplete
reporting, or a display rule. `scripts/check_price_filters.py` reruns the whole chain
with each filter disabled in turn and reports what moves — run it after touching any
threshold, and drop any rule that turns out not to matter.

**Other:** monthly cells below $50k are excluded (a unit value there is rounding);
month-on-month |dln uv| > ln 3 is dropped as a reporting glitch; a stage-month
needs 30% of its covered value matched to the prior month or the step is left as a
gap (flagged `gap`, index carried flat). The 60-code basket excludes photosensitive
devices (solar), same convention as the chain charts.

## 6. Charts

`scripts/plot_prices_net_exports.py` draws three figures into
`results/figures/prices/`: net exports, terms of trade (2021 average = 100), and the
two unit-value legs behind it. They are section 3 of the chart pack — the non-model
view, placed before the factor-model sections.

**One cast of countries, on all three charts.** The candidates are
`gec.config.CHAIN_MAJORS` (TWN KOR CHK JPN USA DEU NLD MYS SGP VNM); a country must then
pass two disclosed tests to be plotted — usable quantity coverage on both flows (≥ 50%),
and a terms-of-trade series moving less than 3.5% in a typical month. Failing either
removes it from **every** chart in the section, not just the price ones, so a reader
follows the same eight names and the same colours from page to page.

That costs something on the net-export chart, where Malaysia (+$86B) and Singapore
(+$78B) are large surpluses with no price problem at all — their figures go in the
caption instead. The alternative, showing them on one chart and not the next, invites
exactly the mistake this section is trying to avoid: comparing two different casts and
reading the difference as a finding.

**A faster view was tried and rejected.** A seasonally adjusted 3-month version of
all three charts (STL on logs, period 12; net exports annualised) is computed and
still in the tables — `m3_sa` rows in `terms_of_trade.csv`, `*_sa` / `*_sa3m` columns
in `net_exports.csv`. Net exports survive it well: the fast line turns a quarter or
two before the 12-month one and stays legible. The price indices do not — at a
3-month window the basket churns, and Korea's terms of trade swing 135 → 66 → 160
inside a single year on codes entering and leaving the window, which is measurement,
not news. Both charts therefore stay on the 12-month view, which also keeps them
comparable to each other.

## 7. Files

| file | grain |
|---|---|
| `results/tables/net_exports.csv` | iso × month: exports, imports, net, and `*_12m` |
| `results/tables/terms_of_trade.csv` | iso × freq × month: px, pm, tot, `*_direct`, coverage |
| `results/tables/price_index_stage_roll12.csv` | iso × flow × stage × month (read this one) |
| `results/tables/price_index_stage_monthly.csv` | same, unsmoothed |
| `results/tables/price_coverage.csv` | iso × flow × stage: usable weight coverage |
| `results/tables/price_index_broad_roll12.csv` | iso × flow × broad stage × month |
| `results/tables/terms_of_trade_broad.csv` | within-stage ToT by broad stage |
| `results/tables/terms_of_trade_net_position.csv` | sell-side over buy-side ToT |
| `data/derived/unit_values_monthly.parquet` | iso × flow × code × month: value, weighted value, kg, uv, placeholder flag (git-ignored) |
