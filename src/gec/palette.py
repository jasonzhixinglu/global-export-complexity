"""Canonical colours for supply-chain stages, shared by every chart.

One palette so a colour means the same thing in the topology map, the network
graph and anywhere else. The hue carries the economics:

  pink    materials consumed per chip (raw materials, wafers and chemicals)
  orange  capital equipment that builds capacity (litho/optics, fab tools)
  green   chip fabrication itself
  blues   the downstream AI-compute codes, darkening along the chain
          (parts/GPU modules -> baseboards -> AI servers)

Colours are saturated rather than pastel so edges stay legible on a phone
screen; FILL gives the matching light tint for filled shapes.
"""
from __future__ import annotations

STAGE = {
    "materials": "#d6337f",     # pink
    "equipment": "#e8590c",     # orange
    "chips":     "#2f9e44",     # green
    "parts":     "#4dabf7",     # light blue
    "baseboards": "#1971c2",    # mid blue
    "servers":   "#0b3d91",     # navy
}

# fills are each stage colour blended 28% over white: saturated enough to match
# the boldness of the network graph, light enough for black labels inside
# One colour per country, used wherever a country is drawn (stage flow charts,
# network graph, factor-loading paths). Fixed by country, never by rank within a
# chart, so a country keeps its colour across every figure in the pack.
COUNTRY = {
    "CHK": "#d7191c", "CHN": "#d7191c", "HKG": "#f06ba8",
    "USA": "#2a78d6", "USM": "#1b4f9c", "MEX": "#f4692e",
    "TWN": "#00a878", "KOR": "#eda100", "JPN": "#7b3fbf",
    "NLD": "#8c510a", "DEU": "#708238", "SGP": "#17becf",
    "MYS": "#c2185b", "VNM": "#84bd00", "THA": "#607d8b",
    "IRL": "#bdb76b", "PHL": "#b05fd6", "IND": "#d95f0e",
    "IDN": "#66a61e", "CAN": "#e7298a", "GBR": "#386cb0",
    "FRA": "#a6761d", "ITA": "#1b9e77", "POL": "#999933",
    "ESP": "#cc6677", "CHE": "#882255", "BEL": "#44aa99",
    "SWE": "#6699cc", "DNK": "#ccb974", "ISR": "#aa4499",
    "CZE": "#6a3d9a", "HUN": "#b15928",
    "ROW": "#b5b3ac", "Other": "#b5b3ac",
}
COUNTRY_FALLBACK = "#898781"

FILL = {
    "materials": "#f4c6db",
    "equipment": "#f9d0bb",
    "chips":     "#c5e4cb",
    "parts":     "#cde7fd",
    "baseboards": "#bfd8ee",
    "servers":   "#bbc9e0",
}
