"""Assemble the supply-chain chart pack PDF from the current generated figures.

One page per chart: title, a short factual caption (claims match the docs --
measured statements only), and the figure. Sections:
  1  The chain as flows            (topology, dollar overview, country network)
  2  The chain in stages           (one hub chart per stage)
  3  The factor model over time    (AI-compute codes only; schematic first)
  4  Concentration & fragmentation (AI-compute codes only)

Every figure is produced by the scripts noted on its page; rerun those first if
data changed. Output: exports/chart_pack.pdf (committed).

`python scripts/build_chart_pack.py mobile` writes chart_pack_mobile.pdf
instead: phone-width portrait pages (one chart per page, page height sized to
the chart, larger type) for reading on a phone without pinching.

Charts are embedded as VECTOR pages when a .pdf sibling of the .png exists
(the generator scripts save both since 2026-07) -- text and lines stay sharp
at any zoom; the .png is the fallback.
"""
from __future__ import annotations
from io import BytesIO
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.backends.backend_pdf import PdfPages

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gec import config as cfg

EX = cfg.ROOT / "exports"
TV = cfg.RESULTS_DIR / "mfm" / "tvmfm"
NS = cfg.RESULTS_DIR / "network_stats"
OUT = EX / "chart_pack.pdf"

SECTIONS = [
 ("1. The chain as flows",
  "2024 trade flows. China and Hong Kong are counted as one (CHK) throughout. "
  "Stages 1-5 use annual Atlas data; stages 6-8 our monthly panel.",
  [
   (EX/"chain_topology.png",
    "The shape of the chain",
    "Two input branches feed chip making; finished hardware flows out to the "
    "right. Pink inputs are used up per chip; orange equipment builds capacity. "
    "Blue: the three codes of our monthly panel. Circle size grows with the log "
    "of 2024 trade."),
   (EX/"overviews/supply_chain_overview_dollar_coarse_2024.png",
    "The whole chain on one dollar scale",
    "Band width = 2024 dollars. The chips stage dominates; small input flows "
    "are drawn but too thin to see."),
   (EX/"network/supply_chain_network_2024.png",
    "The same flows as a country map",
    "Countries as nodes, flows as edges colored by stage. Shows combined "
    "roles: Mexico takes in chips and parts and ships out servers."),
  ]),
 ("2. The chain in stages",
  "One page per stage: exporters on the left, importers on the right, with the "
  "model's groupings in between. Groupings fit the 2024 flows closely "
  "(R-squared 0.95-0.99).",
  [
   (EX/"hubs_nnf/supply_chain_1_raw_materials_nnf_hubs_2024.png",
    "Stage 1 -- raw materials",
    "Reading guide for all stage pages: left = exporters, right = importers, "
    "middle = the model's export and import groups. Much raw-materials trade "
    "is not chip-related (the codes also cover welding gas, abrasives, "
    "fertilizer inputs), so flows scatter widely."),
   (EX/"hubs_nnf/supply_chain_2_wafers_nnf_hubs_2024.png",
    "Stage 2 -- wafers and wafer inputs",
    "Japan dominates the export side."),
   (EX/"hubs_nnf/supply_chain_3_litho_optics_nnf_hubs_2024.png",
    "Stage 3 -- lithography and optics inputs", ""),
   (EX/"hubs_nnf/supply_chain_4_equipment_nnf_hubs_2024.png",
    "Stage 4 -- fab equipment",
    "Machines, not materials: countries buy these to build capacity, and "
    "their imports rise 6-12 months before chip exports."),
   (EX/"hubs_nnf/supply_chain_5_chips_nnf_hubs_2024.png",
    "Stage 5 -- chips",
    "The biggest stage, and the whole electronics industry -- phones, cars "
    "and PCs, not just AI. Most chips flow to Asian assembly; the China "
    "sphere absorbs about 43%."),
   (EX/"hubs_nnf/supply_chain_6_parts_nnf_hubs_2024.png",
    "Stage 6 -- parts and GPU modules (847330)", ""),
   (EX/"hubs_nnf/supply_chain_7_baseboards_nnf_hubs_2024.png",
    "Stage 7 -- baseboards (847180)", ""),
   (EX/"hubs_nnf/supply_chain_8_servers_nnf_hubs_2024.png",
    "Stage 8 -- AI servers (847150)", ""),
  ]),
 ("3. The factor model over time -- AI-compute codes only",
  "This section uses only the three blue codes (parts/GPU modules, baseboards, "
  "AI servers), monthly from 2017. Unless the page says otherwise, China and "
  "Hong Kong are counted as one. Shaded bands mark the periods between "
  "structural breaks.",
  [
   (EX/"mfm_schematic.png",
    "How the model works",
    "The one idea behind every page that follows."),
   (TV/"chn_hkg_bloc/ai_compute/drift.png",
    "When the network changed shape",
    "The line measures how much the export groupings moved from one month to "
    "the next. Flat for six years, then: Aug 2023 (AI demand), Oct 2024 (the "
    "quarter memory export controls were signaled), Sep 2025."),
   (TV/"chn_hkg_bloc/ai_compute/loadings_export.png",
    "Who is in each export group",
    "At Oct 2024 the China group loses its separate identity and a "
    "Singapore-led group appears."),
   (TV/"chn_hkg_bloc/ai_compute/loadings_import.png",
    "Who is in each import group",
    "The import side is steady: a US group, a Mexico group, a Taiwan group, "
    "and the rest of the world."),
   (TV/"chn_hkg_bloc/ai_compute/factors.png",
    "Dollars between groups, month by month",
    "Three of the sixteen channels carry the AI boom: Taiwan to the US, and "
    "both legs of the US-Mexico assembly loop. The rest are flat."),
   (TV/"by_country/ai_compute/drift.png",
    "Same, with every country separate",
    "Without merging China and Hong Kong there is one break in nine years: "
    "Aug 2023. Demand changed the country-level structure; policy did not."),
   (TV/"by_country/847330/drift.png",
    "Parts only (847330)",
    "91 months without a break -- the stable base layer of the network."),
   (TV/"chnhkg_usamex_blocs/ai_compute/drift.png",
    "With both blocs merged",
    "Merging China+Hong Kong and US+Mexico hides churn inside each bloc and "
    "isolates what happens between them. The breaks line up with policy: the "
    "2019 tariff war, the Oct 2022 export controls, the Apr 2025 tariffs."),
   (TV/"chnhkg_usamex_blocs/ai_compute/loadings_export.png",
    "The tariff signature",
    "After Apr 2025 the two blocs move together on a single factor -- seen at "
    "no other break."),
  ]),
 ("4. Concentration & fragmentation -- AI-compute codes only",
  "Monthly measures built on top of the model, for the three blue codes only. "
  "Dotted lines mark Jul 2023 and Apr 2025. Interpretation: "
  "results/network_stats/findings.md.",
  [
   (NS/"ai_compute/fragmentation.png",
    "Two meanings of fragmentation",
    "Left: do the model's groups overlap (a technical check, little economic "
    "signal). Right: the share of trade crossing between the China and US "
    "blocs -- down about 70% since 2017, in two steps (2019, then 2023 on), "
    "with no recovery between."),
   (NS/"ai_compute/decomposition.png",
    "Concentration, taken apart",
    "Overall concentration splits exactly into three parts. The interesting "
    "one asks: do concentrated sellers ship to concentrated buyers? Mildly "
    "yes, peaking around 2019, fading through the AI era."),
   (NS/"ai_compute/linkage.png",
    "One buyer or many?",
    "Left: does each export group sell into one import group or several. "
    "Right: a data-quality check, elevated during the 2023-24 transition."),
   (NS/"847180/fragmentation.png",
    "Baseboards: the sharpest split",
    "The cross-bloc share collapses about 20x from its 2021 peak -- the code "
    "most exposed to export controls."),
   (NS/"847330/fragmentation.png",
    "Parts: still shared",
    "The cross-bloc share halves but stays the highest of the three codes: "
    "the parts trade remains the layer both blocs still share."),
  ]),
]


from pypdf import PdfReader, PdfWriter, Transformation, PageObject

PT = 72.0
W = 6.0  # phone page width, inches


def _wrap(text, width):
    import textwrap
    return "\n".join(textwrap.wrap(text, width)) if text else ""


def _mpl_page(w_in, h_in, draw):
    """Render a matplotlib figure to a single vector PDF page object."""
    fig = plt.figure(figsize=(w_in, h_in))
    draw(fig)
    buf = BytesIO()
    fig.savefig(buf, format="pdf")
    plt.close(fig)
    return PdfReader(buf).pages[0]


def _chart_src(img_path):
    """The chart as a PDF page: vector sibling if present, else the PNG wrapped."""
    vec = Path(img_path).with_suffix(".pdf")
    if vec.exists():
        return PdfReader(str(vec)).pages[0]
    img = mpimg.imread(img_path)
    w_in, h_in = 10.0, 10.0 * img.shape[0] / img.shape[1]

    def draw(fig):
        ax = fig.add_axes([0, 0, 1, 1])
        ax.imshow(img)
        ax.axis("off")
    return _mpl_page(w_in, h_in, draw)


def _compose(writer, header, chart, page_w, page_h, chart_box):
    """Blank page + header at top + chart scaled into chart_box (x, y, w, h)."""
    target = PageObject.create_blank_page(None, page_w, page_h)
    hh = float(header.mediabox.height)
    target.merge_transformed_page(header, Transformation().translate(0, page_h - hh))
    sw, sh = float(chart.mediabox.width), float(chart.mediabox.height)
    x, y, bw, bh = chart_box
    s = min(bw / sw, bh / sh)
    tx = x + (bw - s * sw) / 2
    ty = y + (bh - s * sh) / 2
    target.merge_transformed_page(chart, Transformation().scale(s).translate(tx, ty))
    writer.add_page(target)


def page(writer, img_path, title, caption, section):
    pw, ph = 11.69 * PT, 8.27 * PT
    head_in = 1.15 if caption else 0.65

    def draw(fig):
        fig.text(0.06, 0.90, title, fontsize=15, weight="bold", va="top")
        fig.text(0.94, 0.90, section, fontsize=8, color="#888", va="top", ha="right")
        if caption:
            fig.text(0.06, 0.55, _wrap(caption, 150), fontsize=9, va="top", color="#333")
    header = _mpl_page(11.69, head_in, draw)
    chart = _chart_src(img_path)
    _compose(writer, header, chart, pw, ph,
             (14, 14, pw - 28, ph - head_in * PT - 24))


def divider(writer, title, blurb):
    def draw(fig):
        fig.text(0.5, 0.58, title, fontsize=26, weight="bold", ha="center")
        fig.text(0.5, 0.48, blurb, fontsize=11, ha="center", wrap=True, color="#333")
    writer.add_page(_mpl_page(11.69, 8.27, draw))


def page_mobile(writer, img_path, title, caption, section):
    t = _wrap(title, 44)
    c = _wrap(caption, 62)
    head_in = (0.52 + 0.24 * t.count("\n")
               + (0.16 * (c.count("\n") + 1) + 0.12 if c else 0.06))

    def draw(fig):
        fig.text(0.04, 0.96, section, fontsize=7.5, color="#888", va="top")
        fig.text(0.04, 0.96 - 0.14 / head_in, t, fontsize=13, weight="bold", va="top")
        if c:
            fig.text(0.04, 0.96 - (0.36 + 0.24 * t.count("\n")) / head_in, c,
                     fontsize=9.5, va="top", color="#333")
    header = _mpl_page(W, head_in, draw)
    chart = _chart_src(img_path)
    sw, sh = float(chart.mediabox.width), float(chart.mediabox.height)
    img_h = W * PT * sh / sw
    ph = head_in * PT + img_h + 0.15 * PT
    _compose(writer, header, chart, W * PT, ph, (0, 0.08 * PT, W * PT, img_h))


def divider_mobile(writer, title, blurb):
    b = _wrap(blurb, 58)

    def draw(fig):
        fig.text(0.5, 0.72, title, fontsize=18, weight="bold", ha="center")
        fig.text(0.5, 0.58, b, fontsize=9.5, ha="center", va="top", color="#333")
    writer.add_page(_mpl_page(W, 3.2, draw))


def main(mobile=False):
    missing = [str(p) for _, _, items in SECTIONS for p, _, _ in items
               if not p.exists()]
    if missing:
        sys.exit("missing figures (regenerate first):\n" + "\n".join(missing))
    import datetime
    out = EX / ("chart_pack_mobile.pdf" if mobile else "chart_pack.pdf")
    if not mobile and (EX / "chart_pack.tex").exists() and "--force" not in sys.argv:
        sys.exit("exports/chart_pack.tex is the editable source of the desktop "
                 "pack. Compile it instead: "
                 "python scripts/build_chart_pack_tex.py --compile "
                 "(or pass --force here to overwrite chart_pack.pdf from Python).")
    intro = ("Current state of the analysis. Data: UN Comtrade + TDM monthly "
             "panel (60 HS6 codes, 2017-01..2026-04, checked against Atlas) and "
             "Atlas annual data. Sections: 1 the chain as flows (2024) -- "
             "2 the chain in stages -- 3 the factor model over time -- "
             "4 concentration & fragmentation (sections 3 and 4 use the "
             "AI-compute codes only). Details: docs/data.md, "
             "docs/supply-chain-narrative.md, results/.")
    writer = PdfWriter()
    if mobile:
        def draw_title(fig):
            fig.text(0.5, 0.80, _wrap("AI-compute supply chain: chart pack", 26),
                     fontsize=20, weight="bold", ha="center", va="top")
            fig.text(0.5, 0.55, _wrap(intro, 58), fontsize=9.5, ha="center",
                     va="top", color="#333")
            fig.text(0.5, 0.08, datetime.date.today().isoformat(),
                     fontsize=9, ha="center", color="#888")
        writer.add_page(_mpl_page(W, 4.6, draw_title))
        for title, blurb, items in SECTIONS:
            divider_mobile(writer, title, blurb)
            for p, t, c in items:
                page_mobile(writer, p, t, c, title)
    else:
        def draw_title(fig):
            fig.text(0.5, 0.70, "AI-compute supply chain: chart pack",
                     fontsize=28, weight="bold", ha="center")
            fig.text(0.5, 0.62, _wrap(intro, 95),
                     fontsize=11, ha="center", va="top", color="#333")
            fig.text(0.5, 0.40, datetime.date.today().isoformat(),
                     fontsize=10, ha="center", color="#888")
        writer.add_page(_mpl_page(11.69, 8.27, draw_title))
        for title, blurb, items in SECTIONS:
            divider(writer, title, blurb)
            for p, t, c in items:
                page(writer, p, t, c, title)
    with open(out, "wb") as f:
        writer.write(f)
    n = 1 + sum(1 + len(items) for _, _, items in SECTIONS)
    vec = sum(1 for _, _, items in SECTIONS for p, _, _ in items
              if Path(p).with_suffix(".pdf").exists())
    tot = sum(len(items) for _, _, items in SECTIONS)
    print(f"{out} written: {n} pages ({vec}/{tot} charts vector)")


if __name__ == "__main__":
    main(mobile="mobile" in sys.argv[1:])
