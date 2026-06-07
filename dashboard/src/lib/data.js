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
      getJSON('techai_bilateral.json').catch(() => null),
    ]).then(([meta, series, coverage, anchors, techai, pciProducts, gmm, gmmBilateral, countryProducts, techaiBilateral]) => {
      if (!alive) return
      // index helpers
      const byIso = Object.fromEntries(meta.countries.map(c => [c.iso3, c]))
      const colorByIso = {}
      meta.countries.forEach((c, i) => { colorByIso[c.iso3] = i })
      setData({ meta, series, coverage, anchors, techai, pciProducts, gmm, gmmBilateral, countryProducts, techaiBilateral, byIso, colorByIso })
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

// Combine mixtures into one (a value-weighted sum is itself a mixture): component weights
// scale by each entry's total, so the combined shape integrates to 1 and total = sum of totals.
export function aggregateMixtures(entries) {
  const params = []
  let total = 0
  for (const e of entries) {
    if (!e || !e.params || e.total == null) continue
    for (const [w, mu, sd] of e.params) params.push([w * e.total, mu, sd])
    total += e.total
  }
  return params.length ? { params, total } : { params: null, total: null }
}

// ISO3s in a region (from the displayed top-N universe), excluding any explicitly-selected ones
// so a region bloc and an individually-picked member never double-count.
export function membersOf(data, region, excludeIsos = []) {
  const ex = new Set(excludeIsos)
  return data.meta.countries.filter(c => c.region === region && !ex.has(c.iso3)).map(c => c.iso3)
}

// Build chart rows over the chosen grid. `items` is a mix of ISO3 codes and region blocs
// ('@<Region>'); a bloc aggregates its member countries (minus any individually-selected ones).
// measure: 'share' | 'value' | 'density'; level: 'low'|'med'|'high'; flow: 'export'|'import'
export function buildRows(data, items, year, measure, level = 'med', flow = 'export') {
  const { meta, series, gmm } = data
  const y = String(year)
  const selIsos = items.filter(i => i[0] !== '@')

  if (measure === 'share') {
    const grid = meta.shareGrid
    const shF = series.share[flow] || series.share.export || series.share
    const sh = shF[level] || shF.med || shF
    const at = (item, gi) => {
      if (item[0] === '@') {                       // region bloc = sum of member shares
        let s = 0, any = false
        for (const m of membersOf(data, item.slice(1), selIsos)) {
          const v = sh[m]?.[y]?.[gi]; if (v != null) { s += v; any = true }
        }
        return any ? s : null
      }
      return sh[item]?.[y]?.[gi] ?? null
    }
    return grid.map((pci, gi) => {
      const row = { pci }; for (const it of items) row[it] = at(it, gi); return row
    })
  }

  // density / value: reconstruct from Gaussian mixtures on a fine analytic grid
  const grid = meta.kdeGrid, lo = grid[0], hi = grid[grid.length - 1], N = 400
  const fine = Array.from({ length: N }, (_, i) => lo + (hi - lo) * i / (N - 1))
  const totF = series.totalB[flow] || series.totalB.export || series.totalB
  const mixF = gmm?.mix?.[flow] || gmm?.mix?.export || {}
  const b = gmm?.blur?.[level] ?? gmm?.blur?.med ?? 0.10
  const resolve = (item) => item[0] === '@'
    ? aggregateMixtures(membersOf(data, item.slice(1), selIsos).map(m => ({ params: mixF[m]?.[y], total: totF[m]?.[y] })))
    : { params: mixF[item]?.[y] || null, total: totF[item]?.[y] ?? null }
  const curves = {}
  for (const it of items) {
    const { params, total } = resolve(it)
    if (!params) { curves[it] = null; continue }
    const dens = mixtureDensity(params, b, fine)
    curves[it] = measure === 'value' ? (total != null ? dens.map(d => d * total) : null) : dens
  }
  return fine.map((pci, gi) => {
    const row = { pci }; for (const it of items) row[it] = curves[it] ? curves[it][gi] : null; return row
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
  return aggregateMixtures(members.map(m => corridorOf(data, anchor, m, year, role)))
}

// Build corridor chart rows for one anchor vs several pre-resolved `partySeries` = [{name,params,total}].
// Each party may be a single corridor or an aggregated bloc (see aggregateCorridors).
//   measure 'density' -> each party's normalized shape (lines), + anchor total shape (ref)
//   measure 'value'   -> shape x party total ($B per PCI), + anchor total value (ref)
//   measure 'share'   -> party value density / anchor total value density (% of the anchor's flow by PCI)
// role 'origin' => anchor exports (export distribution is the denominator); 'dest' => imports.
// All counterparties of an anchor that have a stored corridor in a given year/role.
export function allCounterparties(data, anchor, year, role = 'origin') {
  const bil = data.gmmBilateral
  if (!bil) return []
  const y = String(year)
  if (role === 'origin') return Object.keys(bil.mix?.[anchor] || {}).filter(d => bil.mix[anchor][d]?.[y])
  return Object.keys(bil.mix || {}).filter(o => bil.mix[o]?.[anchor]?.[y])
}

export function buildCorridorRows(data, anchor, role, year, partySeries, measure, level = 'med') {
  const grid = fineGrid(data)
  const b = (data.gmmBilateral?.blur || data.gmm?.blur || {})[level] ?? 0.10
  const y = String(year)
  const cflow = role === 'origin' ? 'export' : 'import'

  // SHARE denominator = the anchor's TOTAL flow built from the SAME corridor mixtures (sum over all
  // counterparties), so disjoint selected parties sum to <=100% and all parties sum to exactly 100%.
  // (Using the independently-fit country GMM here makes regions overshoot 100%.)
  let denomVal = null
  if (measure === 'share') {
    const agg = aggregateCorridors(data, anchor, allCounterparties(data, anchor, year, role), year, role)
    denomVal = (agg.params && agg.total != null) ? mixtureDensity(agg.params, b, grid).map(s => s * agg.total) : null
  }
  // country-level GMM as the dashed reference (density / value modes only)
  const aParams = data.gmm?.mix?.[cflow]?.[anchor]?.[y]
  const aTotal = data.series?.totalB?.[cflow]?.[anchor]?.[y]
  const aShape = aParams ? mixtureDensity(aParams, b, grid) : null
  const aValue = (aShape && aTotal != null) ? aShape.map(d => d * aTotal) : null

  const cur = {}
  for (const s of partySeries) {
    if (!s.params) { cur[s.name] = null; continue }
    const shape = mixtureDensity(s.params, b, grid)
    if (measure === 'value') cur[s.name] = s.total != null ? shape.map(d => d * s.total) : null
    else if (measure === 'share') cur[s.name] = (s.total != null && denomVal)
      ? shape.map((d, i) => denomVal[i] > 1e-9 ? (d * s.total) / denomVal[i] : 0) : null
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
