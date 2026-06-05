// Loads the precomputed static JSON and exposes helpers.
import { useEffect, useState } from 'react'

const BASE = `${import.meta.env.BASE_URL}data/`

async function getJSON(name) {
  const res = await fetch(`${BASE}${name}`)
  if (!res.ok) throw new Error(`failed to load ${name}: ${res.status}`)
  return res.json()
}

// One-shot loader for the whole dataset (small enough to fetch up front).
export function useDataset() {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  useEffect(() => {
    let alive = true
    Promise.all([
      getJSON('meta.json'), getJSON('series.json'),
      getJSON('coverage.json'), getJSON('anchors.json'),
    ]).then(([meta, series, coverage, anchors]) => {
      if (!alive) return
      // index helpers
      const byIso = Object.fromEntries(meta.countries.map(c => [c.iso3, c]))
      const colorByIso = {}
      meta.countries.forEach((c, i) => { colorByIso[c.iso3] = i })
      setData({ meta, series, coverage, anchors, byIso, colorByIso })
    }).catch(e => alive && setError(e))
    return () => { alive = false }
  }, [])
  return { data, error }
}

// Build chart rows: array over the chosen grid, each row {pci, [iso3]: value}.
// measure: 'share' | 'value' | 'density'
export function buildRows(data, isos, year, measure) {
  const { meta, series } = data
  const grid = measure === 'share' ? meta.shareGrid : meta.kdeGrid
  const y = String(year)
  return grid.map((pci, gi) => {
    const row = { pci }
    for (const iso of isos) {
      if (measure === 'share') {
        row[iso] = series.share[iso]?.[y]?.[gi] ?? null
      } else if (measure === 'density') {
        row[iso] = series.density[iso]?.[y]?.[gi] ?? null
      } else { // value = density * total ($B)
        const d = series.density[iso]?.[y]?.[gi]
        const t = series.totalB[iso]?.[y]
        row[iso] = (d != null && t != null) ? d * t : null
      }
    }
    return row
  })
}

export const MEASURES = {
  share:   { label: 'Market share', unit: '% of world exports', stack: true },
  value:   { label: 'Export value', unit: '$B per PCI unit',    stack: true },
  density: { label: 'Distribution', unit: 'share of exports (normalized)', stack: false },
}
