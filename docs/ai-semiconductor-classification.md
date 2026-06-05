# AI- and semiconductor-related export classifications

Two external HS-code definitions for tagging "AI-related" trade, recorded in
`src/gec/classifications.py`. They sit at different points on the AI hardware stack.

## 1. Fed — narrow "AI infrastructure / AI compute" (HS6)

From the FEDS Note *"The Global Trade Effects of the AI Infrastructure Boom"* (2026-02-13). A
deliberately tight basket of the AI-compute hardware that drives the data-center boom:

| HS6 | Product | Example |
|---|---|---|
| 8471.50 | ADP processing units | NVIDIA DGX-class AI servers |
| 8471.80 | Other ADP units | HGX server baseboards |
| 8473.30 | Parts/accessories of 8471 machines | GPU / accelerator cards |

The authors note this **under-counts** AI trade (omits relevant products) and can **over-count**
(these codes also carry non-AI computers/parts). They prefer it over the broader WTO definition
(~100 lines) which "obscures smaller AI subcategories and mixes AI with non-AI products."

## 2. OECD — semiconductor value chain (HS 2017)

From OECD (2025), *"Mapping the semiconductor value chain"* (via the Mexico semiconductor report).
~50 HS6 codes grouped by value-chain stage — from inputs through equipment to finished chips:

- **Chips** (finished devices/ICs): 8541xx (diodes, transistors, thyristors, crystals, parts),
  8542xx (ICs: processors, memories, amplifiers, parts), plus 852351/52/59, 853290, 853390.
- **Photosensitive devices**: 854140, 854150.
- **Raw materials**: silicon (280461), gases (280421/29), SiC (284920), gallium/germanium
  (811292/99), borates, arsenic, etc.
- **Manufacturing equipment**: 8486xx (the dedicated semiconductor/wafer/FPD/mask tools), plus
  filtration (8421xx), metrology (903082/84), etc.
- **Foundry inputs**: optics/lenses/filters (9001/9002), electron microscopes (9012), inspection
  (903141).
- **Wafer inputs**: photographic plates/film (3701), silicon wafers (381800).

See the module for the full code→description map and category groupings.

## Using these with our data — important caveats

- **Granularity.** Both are HS6; our main surfaces are **HS4**. For a faithful AI/semiconductor
  cut, analyze at HS6 against the Atlas HS6 files (`hs92_country_product_year_6`, and the bilateral
  HS6 files we already downloaded). `classifications.hs4_set()` gives a coarse HS4 fallback, but at
  HS4 e.g. 8471 also sweeps in non-AI computers — noisy.
- **HS revision.** OECD uses HS2017, the Fed a recent revision; the Atlas is **HS92**. At HS6 an
  HS2017→HS92 concordance is needed; at HS4 most of these headings (8471, 8473, 8541, 8542, 8486,
  9030, 9012, 3701, 3818 …) are revision-stable, so the *headings* map but the *subheadings* don't.
- **Interpretation.** "AI compute" (Fed) is a downstream slice; the OECD set is the whole upstream
  chain. They answer different questions (who exports AI servers vs. who supplies the chip
  ecosystem) and are best kept as separate baskets.

## Possible next steps

1. **Thematic basket analysis at HS6** — pull the Atlas HS6 origin file, restrict to each basket,
   and compute its export value / market share by country and year (and complexity, since each HS6
   maps to a PCI). "Who's winning AI-compute exports / the semiconductor chain, and how complex are
   those exports?"
2. **Dashboard overlay** — highlight basket products on the PCI axis, or a dedicated "AI &
   semiconductors" view, once we decide HS6 vs HS4.
