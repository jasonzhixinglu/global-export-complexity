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
      getJSON('gmm.json').catch(() => null),
    ]).then(([meta, series, coverage, anchors, techai, pciProducts, gmm]) => {
      if (!alive) return
      // index helpers
      const byIso = Object.fromEntries(meta.countries.map(c => [c.iso3, c]))
      const colorByIso = {}
      meta.countries.forEach((c, i) => { colorByIso[c.iso3] = i })
      setData({ meta, series, coverage, anchors, techai, pciProducts, gmm, byIso, colorByIso })
    }).catch(e => alive && setError(e))
    return () => { alive = false }
  }, [])
  return { data, error }
}

const SQRT2PI = Math.sqrt(2 * Math.PI)

// Reconstruct a country's PCI distribution from its stored Gaussian mixture, evaluated
// on `grid`.  Smoothness is a render-time blur: sigma_k -> sqrt(sigma_k^2 + b^2), so one
// stored mixture yields the whole Low/Med/High continuum.  Integrates to ~1 (a shape).
function mixtureDensity(params, b, grid) {
  let wsum = 0
  for (const p of params) wsum += p[0]
  if (wsum <= 0) return grid.map(() => 0)
  return grid.map((x) => {
    let s = 0
    for (const [w, mu, sd] of params) {
      const sp = Math.sqrt(sd * sd + b * b)
      const z = (x - mu) / sp
      s += (w / wsum) * Math.exp(-0.5 * z * z) / (sp * SQRT2PI)
    }
    return s
  })
}

// Build chart rows: array over the chosen grid, each row {pci, [iso3]: value}.
// measure: 'share' | 'value' | 'density'; level: 'low'|'med'|'high'; flow: 'export'|'import'
export function buildRows(data, isos, year, measure, level = 'med', flow = 'export') {
  const { meta, series, gmm } = data
  const grid = measure === 'share' ? meta.shareGrid : meta.kdeGrid
  const y = String(year)

  if (measure === 'share') {
    const shF = series.share[flow] || series.share.export || series.share
    const sh = shF[level] || shF.med || shF
    return grid.map((pci, gi) => {
      const row = { pci }
      for (const iso of isos) row[iso] = sh[iso]?.[y]?.[gi] ?? null
      return row
    })
  }

  // density / value: reconstruct each country's curve from its Gaussian mixture.
  // The mixture is analytic, so render on a FINE grid (decoupled from any stored grid)
  // for a genuinely smooth curve -- evaluating a handful of Gaussians is cheap.
  const lo = grid[0], hi = grid[grid.length - 1], N = 400
  const fine = Array.from({ length: N }, (_, i) => lo + (hi - lo) * i / (N - 1))
  const totF = series.totalB[flow] || series.totalB.export || series.totalB
  const mixF = gmm?.mix?.[flow] || gmm?.mix?.export || {}
  const b = gmm?.blur?.[level] ?? gmm?.blur?.med ?? 0.10
  const curves = {}
  for (const iso of isos) {
    const params = mixF[iso]?.[y]
    if (!params) { curves[iso] = null; continue }
    const dens = mixtureDensity(params, b, fine)          // shape, integrates to ~1
    if (measure === 'value') {
      const t = totF[iso]?.[y]
      curves[iso] = (t != null) ? dens.map(d => d * t) : null   // $B per PCI unit
    } else {
      curves[iso] = dens
    }
  }
  return fine.map((pci, gi) => {
    const row = { pci }
    for (const iso of isos) row[iso] = curves[iso] ? curves[iso][gi] : null
    return row
  })
}

export const MEASURES = {
  share:   { label: 'Market share', unit: '% of world trade', stack: true },
  value:   { label: 'Value ($)',    unit: '$B per PCI unit',  stack: true },
  density: { label: 'Distribution', unit: 'share of trade (normalized)', stack: false },
}
