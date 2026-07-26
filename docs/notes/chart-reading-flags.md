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
