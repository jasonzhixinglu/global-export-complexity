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

FILL = {
    "materials": "#fbe4ef",
    "equipment": "#fdeade",
    "chips":     "#e6f5ea",
    "parts":     "#e4f1fd",
    "baseboards": "#dbe9f8",
    "servers":   "#d9e2f2",
}
