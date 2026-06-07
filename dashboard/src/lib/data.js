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
      getJSON('gmm_bilateral.json').catch(() => null),
      getJSON('country_products.json').catch(() => null),
    ]).then(([meta, series, coverage, anchors, techai, pciProducts, gmm, gmmBilateral, countryProducts]) => {
      if (!alive) return
      // index helpers
      const byIso = Object.fromEntries(meta.countries.map(c => [c.iso3, c]))
      const colorByIso = {}
      meta.countries.forEach((c, i) => { colorByIso[c.iso3] = i })
      setData({ meta, series, coverage, anchors, techai, pciProducts, gmm, gmmBilateral, countryProducts, byIso, colorByIso })
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
  value:   { label: 'Value ($B)',   unit: '$B per PCI unit',  stack: true },
  density: { label: 'Distribution', unit: 'share of trade (normalized)', stack: false },
}

// ---- Bilateral corridors (gmm_bilateral.json) ----------------------------------------------

// A fine evaluation grid spanning the stored PCI endpoints (analytic mixtures -> render smooth).
export function fineGrid(data, n = 400) {
  const g = data.meta.kdeGrid, lo = g[0], hi = g[g.length - 1]
  return Array.from({ length: n }, (_, i) => lo + (hi - lo) * i / (n - 1))
}

export const ANCHOR_KEY = '__anchor__'

// Aggregate several corridors into one mixture (a destination/origin BLOC, e.g. all of Europe):
// the value-weighted sum of mixtures is a mixture — component weights scale by each corridor's
// total, so the combined shape integrates to 1 and `total` is the bloc's summed value.
export function aggregateCorridors(data, anchor, members, year, role = 'origin') {
  const params = []
  let total = 0
  for (const m of members) {
    const { params: p, total: t } = corridorOf(data, anchor, m, year, role)
    if (!p || t == null) continue
    for (const [w, mu, sd] of p) params.push([w * t, mu, sd])
    total += t
  }
  return params.length ? { params, total } : { params: null, total: null }
}

// Build corridor chart rows for one anchor vs several pre-resolved `partySeries` = [{name,params,total}].
// Each party may be a single corridor or an aggregated bloc (see aggregateCorridors).
//   measure 'density' -> each party's normalized shape (lines), + anchor total shape (ref)
//   measure 'value'   -> shape x party total ($B per PCI), + anchor total value (ref)
//   measure 'share'   -> party value density / anchor total value density (% of the anchor's flow by PCI)
// role 'origin' => anchor exports (export distribution is the denominator); 'dest' => imports.
export function buildCorridorRows(data, anchor, role, year, partySeries, measure, level = 'med') {
  const grid = fineGrid(data)
  const b = (data.gmmBilateral?.blur || data.gmm?.blur || {})[level] ?? 0.10
  const y = String(year)
  const cflow = role === 'origin' ? 'export' : 'import'
  const aParams = data.gmm?.mix?.[cflow]?.[anchor]?.[y]
  const aTotal = data.series?.totalB?.[cflow]?.[anchor]?.[y]
  const aShape = aParams ? mixtureDensity(aParams, b, grid) : null
  const aValue = (aShape && aTotal != null) ? aShape.map(d => d * aTotal) : null

  const cur = {}
  for (const s of partySeries) {
    if (!s.params) { cur[s.name] = null; continue }
    const shape = mixtureDensity(s.params, b, grid)
    if (measure === 'value') cur[s.name] = s.total != null ? shape.map(d => d * s.total) : null
    else if (measure === 'share') cur[s.name] = (s.total != null && aValue)
      ? shape.map((d, i) => aValue[i] > 1e-9 ? Math.min(1, (d * s.total) / aValue[i]) : 0) : null
    else cur[s.name] = shape
  }
  return grid.map((pci, gi) => {
    const row = { pci }
    for (const s of partySeries) row[s.name] = cur[s.name] ? cur[s.name][gi] : null
    if (measure === 'value') row[ANCHOR_KEY] = aValue ? aValue[gi] : null
    else if (measure === 'density') row[ANCHOR_KEY] = aShape ? aShape[gi] : null
    return row
  })
}

// Look up a corridor's stored mixture + total for a given year and perspective.
// role 'origin' => anchor exports to party;  role 'dest' => anchor imports from party.
export function corridorOf(data, anchor, party, year, role = 'origin') {
  const bil = data.gmmBilateral
  if (!bil) return { params: null, total: null }
  const y = String(year)
  const [o, d] = role === 'origin' ? [anchor, party] : [party, anchor]
  return { params: bil.mix?.[o]?.[d]?.[y] || null, total: bil.corridorB?.[o]?.[d]?.[y] ?? null }
}

// List counterparties for an anchor, ranked by corridor value in `year` (for the picker / list).
export function corridorCounterparties(data, anchor, year, role = 'origin') {
  const bil = data.gmmBilateral
  if (!bil) return []
  const y = String(year)
  const out = []
  for (const b of bil.blocs) {
    if (b === anchor) continue
    const t = role === 'origin' ? bil.corridorB?.[anchor]?.[b]?.[y] : bil.corridorB?.[b]?.[anchor]?.[y]
    if (t != null && t > 0) out.push({ iso: b, valueB: t })
  }
  return out.sort((a, b) => b.valueB - a.valueB)
}

export const CORRIDOR_MEASURES = {
  share:   { label: 'Partner share', stack: true }, // % of anchor's flow to each counterparty, by PCI
  value:   { label: 'Value ($B)', stack: true },
  density: { label: 'Distribution', stack: false },
}
