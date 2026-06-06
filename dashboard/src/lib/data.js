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
      getJSON('techai.json').catch(() => null),
      getJSON('pci_products.json').catch(() => null),
    ]).then(([meta, series, coverage, anchors, techai, pciProducts]) => {
      if (!alive) return
      // index helpers
      const byIso = Object.fromEntries(meta.countries.map(c => [c.iso3, c]))
      const colorByIso = {}
      meta.countries.forEach((c, i) => { colorByIso[c.iso3] = i })
      setData({ meta, series, coverage, anchors, techai, pciProducts, byIso, colorByIso })
    }).catch(e => alive && setError(e))
    return () => { alive = false }
  }, [])
  return { data, error }
}

// Build chart rows: array over the chosen grid, each row {pci, [iso3]: value}.
// measure: 'share' | 'value' | 'density'; level: 'low'|'med'|'high'; flow: 'export'|'import'
export function buildRows(data, isos, year, measure, level = 'med', flow = 'export') {
  const { meta, series } = data
  const grid = measure === 'share' ? meta.shareGrid : meta.kdeGrid
  const y = String(year)
  const shF = series.share[flow] || series.share.export || series.share
  const deF = series.density[flow] || series.density.export || series.density
  const totF = series.totalB[flow] || series.totalB.export || series.totalB
  const sh = shF[level] || shF.med || shF
  const de = deF[level] || deF.med || deF
  return grid.map((pci, gi) => {
    const row = { pci }
    for (const iso of isos) {
      if (measure === 'share') {
        row[iso] = sh[iso]?.[y]?.[gi] ?? null
      } else if (measure === 'density') {
        row[iso] = de[iso]?.[y]?.[gi] ?? null
      } else { // value = density * total ($B)
        const d = de[iso]?.[y]?.[gi]
        const t = totF[iso]?.[y]
        row[iso] = (d != null && t != null) ? d * t : null
      }
    }
    return row
  })
}

export const MEASURES = {
  share:   { label: 'Market share', unit: '% of world trade', stack: true },
  value:   { label: 'Value ($)',    unit: '$B per PCI unit',  stack: true },
  density: { label: 'Distribution', unit: 'share of trade (normalized)', stack: false },
}
