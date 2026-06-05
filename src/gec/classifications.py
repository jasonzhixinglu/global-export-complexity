"""AI- and semiconductor-related HS product classifications.

Two external definitions, kept as code sets so we can tag/filter trade by theme.

IMPORTANT granularity note: both are defined at HS6 in recent HS revisions (HS2017 for
OECD; unspecified-but-recent for the Fed). Our main pipeline is HS92 at HS4. Use these at
HS6 against the Atlas HS6 files (hs92_country_product_year_6 / bilateral) for fidelity; the
hs4_set() helper gives a coarser HS4 approximation (e.g. 8542 captures all integrated
circuits but 8471 also sweeps in non-AI computers). HS2017->HS92 concordance still applies
at HS6; at HS4 most of these headings are revision-stable.

Sources:
- Fed FEDS Note, "The Global Trade Effects of the AI Infrastructure Boom" (2026-02-13):
  https://www.federalreserve.gov/econres/notes/feds-notes/the-global-trade-effects-of-the-ai-infrastructure-boom-20260213.html
- OECD (2025), "Mapping the semiconductor value chain" (HS 2017), via the Mexico
  semiconductor ecosystem report:
  https://www.oecd.org/en/publications/promoting-the-development-of-the-semiconductor-ecosystem-in-mexico_02c81dec-en/full-report/list-of-harmonized-system-hs-codes-for-semiconductor-related-products_1369575a.html
  https://doi.org/10.1787/4154cdbf-en
"""
from __future__ import annotations

# --- Fed: narrow "AI infrastructure / AI compute" basket (HS6) -------------
# The authors deliberately use a tight 3-code set (AI servers + accelerator cards) over the
# broader ~100-line WTO definition, noting it may both under- and over-count AI trade.
AI_COMPUTE_FED = {
    "847150": "ADP processing units, n.e.s. (AI servers, e.g. NVIDIA DGX)",
    "847180": "Other units of automatic data-processing machines (e.g. HGX baseboards)",
    "847330": "Parts & accessories of heading 8471 machines (e.g. GPU / accelerator cards)",
}

# --- OECD: semiconductor value chain (HS 2017), grouped by stage -----------
SEMICONDUCTOR_OECD = {
    "Chips": {
        "854110": "Diodes (other than photosensitive / LED)",
        "854121": "Transistors, dissipation < 1 W",
        "854129": "Transistors, dissipation >= 1 W",
        "854130": "Thyristors, diacs, triacs",
        "854160": "Mounted piezo-electric crystals",
        "854190": "Parts of semiconductor / photosensitive devices",
        "854231": "ICs: processors and controllers",
        "854232": "ICs: memories",
        "854233": "ICs: amplifiers",
        "854239": "ICs: other (n.e.c.)",
        "854290": "Parts of electronic integrated circuits",
        "852351": "Solid-state non-volatile storage (flash)",
        "852352": "Smart cards (with ICs)",
        "852359": "Semiconductor media, unrecorded",
        "853290": "Parts of electrical capacitors",
        "853390": "Parts of electrical resistors",
    },
    "Photosensitive devices": {
        "854140": "Photosensitive devices incl. PV cells, LEDs",
        "854150": "Photosensitive semiconductor devices, n.e.s.",
    },
    "Raw materials": {
        "252800": "Natural borates",
        "280421": "Argon",
        "280429": "Rare gases (excl. argon)",
        "280461": "Silicon, >= 99.99%",
        "280480": "Arsenic",
        "281000": "Oxides of boron; boric acids",
        "281212": "Phosphorus oxychloride",
        "282560": "Germanium / zirconium oxides",
        "283325": "Copper sulphates",
        "284011": "Borax, anhydrous",
        "284019": "Borax, other",
        "284920": "Silicon carbide",
        "285000": "Hydrides, nitrides, silicides, borides",
        "811292": "Gallium, germanium, indium, etc., unwrought",
        "811299": "Articles of gallium, germanium, indium, etc.",
    },
    "Manufacturing equipment": {
        "841459": "Fans / blowers",
        "841950": "Heat-exchange units",
        "842129": "Filtering / purifying machinery (liquids)",
        "842139": "Filtering / purifying machinery (gases)",
        "842199": "Parts of filtering / purifying machinery",
        "848610": "Machines for semiconductor boules / wafers",
        "848620": "Machines for semiconductor devices / ICs",
        "848630": "Machines for flat panel displays",
        "848640": "Machines for masks/reticles, assembly, handling",
        "848690": "Parts & accessories for heading 8486 machines",
        "900699": "Photographic flashlight apparatus",
        "903082": "Instruments to measure/check semiconductor wafers/devices",
        "903084": "Instruments to measure electrical quantities (recording)",
        "903300": "Regulating / controlling instruments",
    },
    "Foundry inputs": {
        "900120": "Polarising material / semiconductor sheets & plates",
        "900190": "Optical elements, unmounted",
        "900219": "Objective lenses",
        "900220": "Optical filters",
        "900290": "Optical elements, mounted",
        "901210": "Electron / proton microscopes, diffraction apparatus",
        "901290": "Parts for electron microscopes",
        "903141": "Optical instruments inspecting semiconductor devices",
    },
    "Wafer inputs": {
        "370130": "Photographic plates & film, flat, > 255 mm",
        "370199": "Photographic plates & film, flat, other",
        "370790": "Photographic chemical goods",
        "381800": "Silicon wafers (doped for electronics)",
    },
}

# Convenience: the OECD "core chip" subset closest to finished semiconductors.
SEMICONDUCTOR_CORE = {**SEMICONDUCTOR_OECD["Chips"], **SEMICONDUCTOR_OECD["Photosensitive devices"]}


def semiconductor_hs6() -> dict[str, str]:
    """Flat {hs6: description} across all OECD categories."""
    out = {}
    for group in SEMICONDUCTOR_OECD.values():
        out.update(group)
    return out


def hs4_set(hs6_codes) -> set[str]:
    """Coarse HS4 approximation of an HS6 code set (first 4 digits). See module note."""
    return {c[:4] for c in hs6_codes}
