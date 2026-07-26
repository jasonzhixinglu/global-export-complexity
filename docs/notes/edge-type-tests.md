# Edge types between stages: tests

Motivation: the firm-level chain anatomy ([firm-level-supply-chain-data.md](firm-level-supply-chain-data.md))
distinguishes inputs that flow per unit of output (consumables) from inputs that
build capacity (equipment) and from complements that converge at an assembly
node (kits). If real, these should have different dynamic signatures in the
panel. Method: year-over-year log changes of 3-month sums (removes trend and
seasonality), cross-correlated at leads; panel_semi_monthly, 2017-01..2026-04.
Equipment = the 9 semi-specific codes (8486xx + metrology); chips = the 16
OECD chip codes; wafers = the 4 wafer-input codes.

## Result 1: in fab countries, wafers are contemporaneous, equipment leads

corr( input imports_t , chip exports_{t+k} ):

| country | input | k=0 | k=6 | k=12 | k=18 | k=24 |
|---|---|---|---|---|---|---|
| TWN | wafers | **0.52** | 0.20 | −0.01 | | |
| TWN | equipment | 0.10 | 0.13 | **0.27** | 0.16 | −0.15 |
| KOR | wafers | **0.23** | −0.02 | −0.47 | | |
| KOR | equipment | 0.30 | **0.42** | 0.34 | −0.02 | −0.49 |

Wafer imports peak at lag zero and die out within a year; equipment imports
peak 6–12 months ahead of chip exports and turn negative at 24–30 months (the
investment cycle: tool purchases precede output growth and fall while output
keeps rising).

## Result 2: the separation does not appear for China

CHN equipment imports vs CHN chip exports: 0.28 / 0.35 / 0.10 / 0.01 / −0.06 at
k = 0/6/12/18/24 — nearly the same profile as its wafer imports (0.19 / 0.29 /
0.11). China's chip exports are dominated by assembly/test output and
re-export, not leading-edge fab output, so the country aggregate does not
isolate the fab investment cycle.

## Result 3: no lead found in the within-stage tier (Zeiss→ASML)

corr( DEU→NLD optics imports_t , NLD 848620 exports_{t+k} ): 0.30 / 0.07 /
0.16 / 0.10 / −0.19 at k = 0/3/6/9/12. Maximum at k=0; no production-pipeline
lead is visible at this aggregation.

## Result 4: the kit is a composition fact, not a monthly-timing fact

corr( KOR→TWN 854232_t , TWN 847180+847330 exports_{t+k} ) is flat at 0.31–0.39
across k = −6..+6. The kit evidence remains the levels-based cross-destination
proportionality (corr(log,log) = 0.83) and the joint repricing documented in
modeling-brainstorm §III.3; monthly shipment timing within the kit is loose.

## What this supports

- The consumable-vs-capacity distinction is measurable in fab countries and is
  the right accounting rule for Layer-2 chain accounting: equipment imports are
  investment, not current intermediates; treating them as intermediates would
  misallocate $249B/yr (2024) of flows.
- Cumulated equipment imports per country can serve as a fab capital-stock
  proxy (a leading series; TWN/KOR lead 6–12 months).
- Stage ordering in data.md §1 is presentation order; combination rules differ
  by edge type. Membership of codes in stages (OECD) is unchanged.

Method is fully specified above (YoY log changes of 3-month sums,
cross-correlated at leads on panel_semi_monthly); ~10 lines of pandas to rerun.
