# Chart-reading flags (running note)

Questions raised while reviewing the chart pack, with the resolution of each.
Started 2026-07-26; append as new flags come up.

1. **Taiwan/Korea appear to import no inputs** (whole-chain overview).
   Resolution: they do — but on the dollar-mode overview the common scale is
   set by the chips stage (~$926B), so the inbound ribbons are drawn at
   sub-pixel height: Japan→Taiwan wafers 2024 = $1.6B (all wafer flows into
   TWN ≈ $2.9B) → ≈0.2% of figure height. The flow is too small to see at that scale,
   not folded — Taiwan clears the fold rule ($10B absolute OR 10% of stage;
   $2.9B vs the $25B wafer stage) and is a named importer node; the ribbon is
   drawn to it, invisibly thin. Part of fab inputs is also produced in the
   fab country itself and never crosses customs. Traded inputs are ~1/30 of
   traded chip output because most of a chip's value is added inside the fab.
   Readable views: normalized overview (equal stage heights), per-stage hub
   charts.

2. **What does folding do to small flows?**
   Resolution (semantics, not a bug): folding collapses sub-threshold
   *countries* into a column's Other node; flows keep their true endpoints and
   Other totals are exact sums. Two distinct reasons a flow can be hard to
   see: its country folded into Other (small share of the stage), or —
   as in item 1 — it is drawn to a named node but at sub-pixel width on the
   dollar scale.

3. **Mexico shows no imports in the intra-assembly stage** (2024 overview).
   Resolution: its 2024 inbound (~$4.8B TWN boards, ~$12.8B USA parts, some
   CHK components) is split across several corridors each near the fold
   threshold of a $220B stage, while its outbound is one fat server ribbon —
   opposite of Taiwan: thin margin pass-through vs large value-added.
   Timing matters: the inbound ramp is 2025 (TWN $16B, USA $25B).

4. **Taiwan's chips seem to flow only to CHK** (chips column).
   Resolution: mostly real — bare chips flow to the Asian assembly complex
   (China sphere absorbs ~43% of the stage); the US buys finished compute
   downstream; TSMC's AI dies are packaged domestically and exit under
   parts/baseboards codes, skipping the chips column entirely. Folding
   sharpens it: the chips stage's 10% threshold ≈ $80B, so all non-CHK
   destinations bundle into Other.

Standing reading rules that come out of 1–4: thin ribbon = small dollars, not
missing data; Other = an exact bundle of sub-threshold counterparties; the
dollar overview answers "where is the money", the normalized overview and
stage hub charts answer "who trades with whom".

5. **Large stage-1 flows into Other — surprising for a focused supply chain.**
   Resolution: the raw-materials codes are generic industrial commodities that
   also feed fabs — rare gases (welding/medical), silicon carbide (abrasives),
   copper sulphate (agriculture), borates (glass/detergents). Customs codes do
   not see purity grade or end use, so most trade in these codes is
   non-semiconductor and disperses across many mid-sized industrial importers,
   each below the fold threshold. The exception: 280461 (silicon >= 99.99%) has
   a purity threshold in its definition and flows concentrate toward fab
   countries. In short: the inputs at the top of the chain are not only used
   for chip making, and the trade data cannot tell the chip-bound share apart.
   The closer a code is to the GPU, the more of its trade is genuinely about
   chips (see data.md section 1).

6. **The US does not stand out as the import hub in the whole-chain overview.**
   Resolution, three parts. (a) The chart never sums a country across columns:
   US inbound is split between chips (small), parts, baseboards, servers and
   equipment, so no single column shows its aggregate, while China's inbound
   is concentrated in the two biggest columns (chips, equipment). (b) Not all
   chips are for AI: the chips stage is the whole electronics industry
   (phones, cars, PCs), the AI slice is a minority of it, and bare AI silicon
   is mostly packaged in Asia rather than imported by the US. In the compute
   codes, the layer closest to AI, the US is unambiguously the import hub
   (about a third of world imports in 2024, 42.5% in 2025, and a dedicated USA
   import factor in every model run). (c) The chart shows 2024; the US share
   and the Taiwan-to-US corridors are much larger in 2025-26.

7. **China appears to be the single largest node overall, most visibly at the
   chips stage.**
   Resolution: faithful, and an electronics fact rather than an AI fact —
   with China in two roles at once, both large. It is the biggest chips
   importer (the China sphere absorbs just over 40% of the stage: TWN chips
   $52B, KOR $45B, CHN-to-HK conduit $72B in 2024, roughly flat as a share),
   and it is also a major chips producer and exporter (17% of stage exports,
   and a leading exporter in several discrete/power codes), with measured
   equipment imports showing capacity still being built. Much of what it
   imports leaves again inside finished electronics whose codes are outside
   this chart, so inbound shows at full size while that outbound is invisible.
   What the data cannot tell us: the share of its chip imports or exports by
   where the die was fabricated — so how much of each role is device assembly
   vs domestic fabrication is not measurable here. In the AI-specific compute
   codes the picture inverts: China's import share is ~5% by 2025 and the US
   is the pole.

8. **The TV-MFM results read as a disorganized set — unclear what is shown,
   in what order, and how the runs break down.**
   The structure that exists (stated nowhere in the outputs themselves, which
   is the problem): the nine runs form a grid of code basket x bloc
   treatment. Baskets: the three codes separately (847150, 847180, 847330)
   and their sum (ai_compute). Bloc treatments, in increasing order of
   netting: by_country (no merging), chn_hkg_bloc (China+HKG merged, the
   preferred basis for interpretation), chnhkg_usamex_blocs (both blocs
   merged, ai_compute only — the policy lens). Every run produces the same
   four figures: drift.png (when the structure breaks — read first),
   loadings_export.png and loadings_import.png (who constitutes each hub,
   era-anchored), factors.png (the 4x4 hub-to-hub dollar intensities), plus
   summary.md with era compositions and cross-era crosswalk tables. Intended
   reading order: chn_hkg_bloc/ai_compute first (the headline run), then
   by_country/ai_compute and by_country/847330 as contrasts (demand break,
   parts stability), then the per-code CHK runs, then the double-bloc run for
   policy dates. The chart pack's section 2 follows roughly this order but
   does not say so.
   Addendum (pack pages ~15-22): the section also switches organizing
   principle midway without announcing it — pages 15-18 are ONE run shown in
   full (AI compute, CHK basis: drift, export loadings, import loadings,
   factors), pages 19-20 are single contrast figures from OTHER runs
   (country-level aggregate; parts), pages 21-22 are the double-bloc policy
   run. Captions identify each run but nothing signals the change from
   "one run, all figures" to "one figure, several runs".

9. **Loadings show sharp breaks but the charts don't say which events they
   align with; some factor-intensity cells grew almost exponentially.**
   Both observations are correct. (a) The figures shade era boundaries but do
   not name events; the mapping lives only in the summaries and the narrative
   (2023-08 = H100 volume shipments; 2024-10 = the quarter the HBM controls
   were signaled, China-bloc hub dissolves, Singapore hub born; 2025-04 =
   tariffs + H20 ban, visible in the double-bloc run). (b) Measured on the
   CHK-basis aggregate run, three of sixteen intensity cells carry the boom
   (2022 avg -> 2026 avg, $B/month units): TWN-hub -> USA-hub 0.04 -> 0.54
   (the dominant AI channel), MEX-hub -> USA-hub 0.09 -> 0.42, and
   USA-hub -> MEX-hub 0.03 -> 0.19 (the two legs of the US-Mexico assembly
   loop). All other cells are flat or drifting: in the demand-programs
   reading, those three cells are the AI build-out program's budget lines and
   the flat cells are what remains of the PC-era programs.

10. **The drift/burst measure: threshold undefined on the chart, bursts
    unexplained, but conceptually useful — constant loadings would imply no
    breaks.**
    What the measure is: for each month, the chordal distance between the
    loading subspaces of two consecutive 12-month windows,
    sqrt(K - ||R'_{t-1} R_t||_F^2) / sqrt(K), in [0,1] — zero when the hub
    space is unchanged, one when it is orthogonal. The threshold (0.20) is a
    fixed tuning constant, chosen by judgment, not derived from a null
    distribution; a companion rule merges calm stretches shorter than 6
    months. There is no significance test behind it. The conceptual point in
    the flag is right: if loadings were constant, drift would sit at a
    sampling-noise floor — and it does, at roughly 0.02-0.08 for the entire
    2018-2023 stretch — so the sustained excursions after mid-2023 are direct
    evidence against loading constancy, which is exactly why the estimation
    is era-anchored rather than a single constant-loading model. What
    explains any individual burst is answered (to the extent it is) by the
    era summaries' crosswalk tables, which show which hubs reorganized at
    that break; the drift series itself only says that the space moved.

11. **The per-stage hub charts are hard to interpret — many kinds of trade
    seem merged into one estimation.**
    Correct on both counts. Two layers of merging are at work. First, each
    stage chart is estimated on a multi-code basket (up to 16 HS6 codes for
    chips), and within even a single HS6 code very different products and
    purposes travel together — the documented within-code spread of exporter
    unit values is 10-100x, and upstream codes carry large non-semiconductor
    trade (item 5). The hubs of a stage chart therefore group countries that
    co-trade for possibly unrelated reasons: AI hardware, commodity
    electronics, and non-chip industrial demand can all sit inside one hub.
    Second, these charts decompose a single year's flow matrix (2024, k=4) —
    they find the dominant blocks of that one cross-section. That is a weaker
    identification than the monthly TV-MFM, where hubs are pinned down by
    co-movement over 100+ months and can be read as spending programs. The
    stage hub charts are best read as "who trades with whom, compressed",
    crisp only where one purpose dominates the basket (wafers, the compute
    codes); the monthly model is where hub interpretation carries weight.
    The documented route to separating varieties inside a code is national
    tariff-line data (the standing top open item in modeling-brainstorm V).
