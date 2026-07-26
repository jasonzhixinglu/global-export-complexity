# Chart-reading flags (running note)

Questions raised while reviewing the chart pack, with the resolution of each.
Items marked "candidate fix" are presentation improvements not yet made.
Started 2026-07-26; append as new flags come up.

1. **Taiwan/Korea appear to import no inputs** (whole-chain overview).
   Resolution: they do — the input stages are $13–38B against $823B of chips,
   so inbound ribbons are hairlines on the dollar scale and sub-threshold
   importers fold into Other; part of fab inputs is also domestic/on-site and
   never crosses customs. The 30:1 output-to-traded-input ratio is the
   value-creation fact, not a data hole. Readable views: normalized overview,
   per-stage hub charts.

2. **What does folding do to small flows?**
   Resolution (semantics, not a bug): folding collapses sub-threshold
   *countries* into a column's Other node; flows keep their true endpoints and
   Other totals are exact sums. Japan→Taiwan wafers plot as Japan→Taiwan,
   thin; Japan→(small destinations) plot as Japan→Other.

3. **Mexico shows no imports in the intra-assembly stage** (2024 overview).
   Resolution: its 2024 inbound (~$4.8B TWN boards, ~$12.8B USA parts, some
   CHK components) is split across several corridors each near the fold
   threshold of a $220B stage, while its outbound is one fat server ribbon —
   opposite of Taiwan: thin margin pass-through vs large value-added.
   Timing matters: the inbound ramp is 2025 (TWN $16B, USA $25B).
   Candidate fix: a 2025 chart edition once every stage's data closes, and/or
   a lower fold threshold for the intra-assembly column.

4. **Taiwan's chips seem to flow only to CHK** (chips column).
   Resolution: mostly real — bare chips flow to the Asian assembly complex
   (China sphere absorbs ~43% of the stage); the US buys finished compute
   downstream; TSMC's AI dies are packaged domestically and exit under
   parts/baseboards codes, skipping the chips column entirely. Folding
   sharpens it: the chips stage's 10% threshold ≈ $80B, so all non-CHK
   destinations bundle into Other.
   Candidate fix: per-column threshold overrides so second-tier chip
   importers (SGP/MYS/KOR/USA) stay named.

Standing reading rules that come out of 1–4: thin ribbon = small dollars, not
missing data; Other = an exact bundle of sub-threshold counterparties; the
dollar overview answers "where is the money", the normalized overview and
stage hub charts answer "who trades with whom".
