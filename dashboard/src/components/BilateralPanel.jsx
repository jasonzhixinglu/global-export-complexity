import { useEffect, useMemo, useState } from 'react'
import {
  ResponsiveContainer, LineChart, Line, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine,
} from 'recharts'
import {
  buildCorridorRows, corridorOf, aggregateCorridors, corridorCounterparties,
  CORRIDOR_MEASURES, ANCHOR_KEY,
} from '../lib/data.js'
import { colorFor, fmtB, fmtPct, fmtPci } from '../lib/format.js'
import { axisColors, tooltipStyle } from '../lib/chartTheme.js'
import { Toggle, YearStepper, CountryPicker } from './Controls.jsx'
import { useDarkMode } from '../lib/useDarkMode.jsx'

export default function BilateralPanel({ data, year, setYear }) {
  const { isDark } = useDarkMode()
  const { meta, byIso, gmmBilateral: bil, pciProducts: pp } = data
  const [role, setRole] = useState('origin')          // 'origin' = exports from; 'dest' = imports to
  const [anchor, setAnchor] = useState('CHN')
  const [parties, setParties] = useState([])
  const [measure, setMeasure] = useState('share')
  const [level, setLevel] = useState(meta.defaultLevel || 'med')
  const [display, setDisplay] = useState('stack')
  const [pickerOpen, setPickerOpen] = useState(false)   // mobile: counterparty list collapsed by default
  const [selectedPci, setSelectedPci] = useState(1.0)
  const ac = axisColors(isDark)

  if (!bil) return <div className="panel p-6 text-sm text-slate-400">Bilateral corridor data not available.</div>

  const y = String(Math.min(bil.years[bil.years.length - 1], Math.max(bil.years[0], year)))
  const nameOf = (iso) => iso === 'ROW' ? 'Rest of world' : (byIso[iso]?.name || iso)
  // '@Region' bloc vs country; a bloc reads "(rest)" when some members are picked individually
  // (the bloc is then that region minus those members, so nothing double-counts).
  const labelOf = (p) => {
    if (p[0] !== '@') return nameOf(p)
    const region = p.slice(1)
    const partial = (regionMembers[region] || []).some(m => selIsos.includes(m))
    return region + (partial ? ' (rest)' : '')
  }
  const cflow = role === 'origin' ? 'export' : 'import'
  const flowWord = role === 'origin' ? 'exports' : 'imports'
  const otherWord = role === 'origin' ? 'destinations' : 'origins'
  const regionsOrder = [...meta.regionsOrder, 'Rest of world']

  // region blocs: group the anchor's counterparties (top-50 members + ROW) by region
  const regionMembers = useMemo(() => {
    const m = {}
    for (const b of bil.blocs) {
      if (b === anchor) continue
      const r = b === 'ROW' ? 'Rest of world' : (byIso[b]?.region || 'Other')
      ;(m[r] ||= []).push(b)
    }
    return m
  }, [bil.blocs, anchor, byIso])
  const regionList = useMemo(() => regionsOrder.filter(r => regionMembers[r]?.length), [regionMembers]) // eslint-disable-line

  const ranked = useMemo(() => corridorCounterparties(data, anchor, Number(y), role),
    [data, anchor, y, role])

  // default selection when anchor / perspective changes: the region blocs (a clean 100% split)
  useEffect(() => {
    setParties(regionList.map(r => '@' + r))
  }, [anchor, role])  // eslint-disable-line react-hooks/exhaustive-deps

  const colorOf = useMemo(() => {
    const m = {}; parties.forEach((p, i) => { m[p] = colorFor(i) }); return m
  }, [parties])
  const cOf = (iso) => colorOf[iso] || '#94a3b8'

  // resolve each selected counterparty -> {name, params, total}. A '@Region' bloc aggregates its
  // members EXCLUDING any individually-selected ones, so blocs and countries can be mixed safely.
  const selIsos = parties.filter(p => p[0] !== '@')
  const partySeries = useMemo(() => parties.map(p => p[0] === '@'
    ? { name: p, ...aggregateCorridors(data, anchor, (regionMembers[p.slice(1)] || []).filter(m => !selIsos.includes(m)), Number(y), role) }
    : { name: p, ...corridorOf(data, anchor, p, Number(y), role) }),
    [parties, data, anchor, regionMembers, y, role])  // eslint-disable-line react-hooks/exhaustive-deps

  const stackable = CORRIDOR_MEASURES[measure].stack
  const stack = stackable && display === 'stack'
  const rows = useMemo(() => buildCorridorRows(data, anchor, role, Number(y), partySeries, measure, level),
    [data, anchor, role, y, partySeries, measure, level])

  // coverage caption
  const totalCorr = ranked.reduce((s, d) => s + d.valueB, 0)
  const selSum = partySeries.reduce((s, ps) => s + (ps.total || 0), 0)
  const countryTot = data.series?.totalB?.[cflow]?.[anchor]?.[y]
  const selShare = totalCorr ? selSum / totalCorr : null
  const cov = countryTot ? totalCorr / countryTot : null

  // PCI product drill-down: the ANCHOR country's largest export/import categories near the
  // selected PCI (top-50 per country-year in country_products.json). Show the 10 nearest by PCI,
  // then sort by value -- a sparse PCI may surface categories somewhat further away. Falls back to
  // global products when the anchor has no per-country data (e.g. the ROW bloc).
  const baseWin = meta.smoothing?.find(s => s.id === level)?.win ?? 0.05
  const vIdx = role === 'origin' ? 2 : 3   // pci_products row = [hs4, pci, exportB, importB]
  const { prods, win, src } = useMemo(() => {
    const MAXD = 0.3   // prefer the anchor's categories within +/-0.3 of the clicked PCI
    const cp = data.countryProducts?.products?.[cflow]?.[anchor]?.[y]
    if (cp && cp.length) {
      const byDist = cp.map(([hs4, pci, val]) => ({ hs4, pci, val }))
        .sort((a, b) => Math.abs(a.pci - selectedPci) - Math.abs(b.pci - selectedPci))
      let near = byDist.filter(p => Math.abs(p.pci - selectedPci) <= MAXD).slice(0, 10)
      if (!near.length) near = byDist.slice(0, 5)   // fallback: nearest categories so it's never empty
      const w = near.length ? Math.max(...near.map(p => Math.abs(p.pci - selectedPci))) : MAXD
      near.sort((a, b) => b.val - a.val)
      return { prods: near, win: w, src: 'country' }
    }
    const list = pp?.byYear?.[y] || []          // fallback: global products window
    if (!list.length) return { prods: [], win: baseWin, src: 'global' }
    let w = baseWin, cand = list.filter(p => Math.abs(p[1] - selectedPci) <= w)
    while (cand.length < 10 && w < 1.5) { w += baseWin; cand = list.filter(p => Math.abs(p[1] - selectedPci) <= w) }
    const prods = cand.sort((a, b) => b[vIdx] - a[vIdx]).slice(0, 10).map(p => ({ hs4: p[0], pci: p[1], val: p[vIdx] }))
    return { prods, win: w, src: 'global' }
  }, [data, pp, y, selectedPci, baseWin, vIdx, anchor, cflow])
  const maxVal = prods.length ? Math.max(...prods.map(p => p.val)) : 1
  const onPick = (e) => { if (e && e.activeLabel != null) setSelectedPci(Number(e.activeLabel)) }

  const yfmt = measure === 'share' ? (v) => `${Math.round(v * 100)}%`
    : measure === 'value' ? (v) => `$${v >= 1000 ? (v / 1000).toFixed(1) + 'T' : Math.round(v) + 'B'}`
      : (v) => v.toFixed(2)
  const vfmt = measure === 'share' ? (v) => fmtPct(v, 1)
    : measure === 'value' ? (v) => fmtB(v, 1) : (v) => v?.toFixed(4)
  // product values: $B for sizeable categories, $M for the small tail ones (avoids "$0.0B")
  const fmtVal = (v) => v >= 0.1 ? fmtB(v, 1) : v > 0 ? `$${Math.max(1, Math.round(v * 1000))}M` : '$0'

  const toggle = (key) => setParties(prev => prev.includes(key) ? prev.filter(x => x !== key) : [...prev, key])
  const onBloc = (region) => toggle('@' + region)

  const corrCountries = bil.blocs.map(b => b === 'ROW'
    ? { iso3: 'ROW', name: 'Rest of world', region: 'Rest of world' }
    : (byIso[b] || { iso3: b, name: b, region: 'Other' }))

  const ChartInner = stack ? AreaChart : LineChart
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-12 gap-3">
      {/* LEFT — perspective, anchor, counterparties */}
      <div className="md:col-span-1 lg:col-span-3 min-w-0">
        <div className="panel p-3 h-full flex flex-col gap-3">
          {/* perspective + anchor on one row: reads "Exports · China" (= China's exports) */}
          <div className="flex items-center gap-2">
            <Toggle value={role} onChange={setRole}
              options={[{ value: 'origin', label: 'Exports' }, { value: 'dest', label: 'Imports' }]} />
            <select value={anchor} onChange={e => setAnchor(e.target.value)}
              className="flex-1 min-w-0 bg-transparent border border-slate-300 dark:border-slate-600 rounded px-2 py-1 text-sm">
              {bil.blocs.map(b => <option key={b} value={b}>{nameOf(b)}</option>)}
            </select>
          </div>
          <div className="flex items-center justify-between">
            <span className="label">Year</span>
            <YearStepper years={bil.years} year={Number(y)} onChange={setYear} />
          </div>
          <div className="border-t border-slate-200 dark:border-slate-800 pt-2 flex flex-col flex-1 min-h-0 gap-2">
            <div className="flex items-center justify-between gap-2">
              <div className="label">{otherWord} · {parties.length}</div>
              <div className="flex items-center gap-2">
                <button onClick={() => setPickerOpen(o => !o)}
                  className="lg:hidden text-[11px] text-indigo-500 hover:text-indigo-400">{pickerOpen ? 'Hide' : 'Edit'}</button>
                <button onClick={() => setParties([])} disabled={!parties.length}
                  className="text-[11px] text-slate-400 hover:text-rose-500 disabled:opacity-40">Clear</button>
              </div>
            </div>
            <div className={`${pickerOpen ? 'flex' : 'hidden'} lg:flex flex-col flex-1 min-h-0 gap-2`}>
              <div className="flex-1 min-h-0 overflow-y-auto pr-1 -mr-1 max-h-[46vh] lg:max-h-none">
                <CountryPicker countries={corrCountries} regionsOrder={regionsOrder}
                  selected={parties} onToggle={toggle} onBloc={onBloc} colorOf={cOf} />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* MIDDLE — corridor distributions / shares */}
      <div className="md:col-span-2 lg:col-span-6 md:order-last lg:order-none min-w-0">
        <div className="panel p-3 h-full">
          <div className="flex flex-wrap items-center gap-x-3 gap-y-2 justify-between mb-2">
            <Toggle value={measure} onChange={setMeasure}
              options={Object.entries(CORRIDOR_MEASURES).map(([k, m]) => ({ value: k, label: m.label }))} />
            <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
              <span className="inline-flex items-center gap-1.5">
                <span className="label">Smoothness</span>
                <Toggle value={level} onChange={setLevel}
                  options={meta.smoothing.map(s => ({ value: s.id, label: s.label }))} />
              </span>
              {stackable && (
                <Toggle value={display} onChange={setDisplay}
                  options={[{ value: 'stack', label: 'Stacked' }, { value: 'lines', label: 'Lines' }]} />
              )}
              <span className="text-[11px] text-amber-500/90 inline-flex items-center gap-1">
                <span className="inline-block w-3 border-t border-dashed border-amber-500" /> click to inspect
              </span>
            </div>
          </div>
          <div className="text-[11px] text-slate-400 mb-1">
            {role === 'origin' ? `${nameOf(anchor)} ${flowWord} → ${otherWord}` : `${otherWord} → ${nameOf(anchor)} ${flowWord}`}, {y}
            {measure === 'share' ? ` · share of ${nameOf(anchor)}’s ${flowWord} by complexity`
              : ` · dashed = ${nameOf(anchor)}’s total`}
          </div>
          <div className="cursor-crosshair">
            <ResponsiveContainer width="100%" height={420}>
              <ChartInner data={rows} margin={{ top: 8, right: 12, bottom: 24, left: 4 }} onClick={onPick}>
                <CartesianGrid stroke={ac.grid} strokeDasharray="2 2" />
                <XAxis dataKey="pci" type="number" domain={['dataMin', 'dataMax']} tickCount={11}
                  tick={{ fill: ac.tick, fontSize: 10 }} tickFormatter={fmtPci}
                  label={{ value: 'Product Complexity Index (PCI)', position: 'insideBottom', offset: -12, fill: ac.tick, fontSize: 11 }} />
                <YAxis tick={{ fill: ac.tick, fontSize: 10 }} tickFormatter={yfmt} width={46}
                  domain={measure === 'share' ? [0, 1] : [0, 'auto']} allowDataOverflow={measure === 'share'} />
                <ReferenceLine x={0} stroke={ac.grid} />
                <ReferenceLine x={selectedPci} stroke="#f59e0b" strokeWidth={1.5} strokeDasharray="4 2" />
                <Tooltip contentStyle={tooltipStyle(isDark)} labelFormatter={(p) => `PCI ${fmtPci(p)}`}
                  formatter={(v, n) => [vfmt(v), n === ANCHOR_KEY ? `${nameOf(anchor)} (total)` : labelOf(n)]} />
                {stack
                  ? parties.map(p => (
                    <Area key={p} type="monotone" dataKey={p} stackId="1" stroke={cOf(p)}
                      fill={cOf(p)} fillOpacity={0.7} strokeWidth={1} isAnimationActive={false} />
                  ))
                  : parties.map(p => (
                    <Line key={p} type="monotone" dataKey={p} stroke={cOf(p)}
                      dot={false} strokeWidth={2} isAnimationActive={false} />
                  ))}
                {measure !== 'share' && (
                  <Line type="monotone" dataKey={ANCHOR_KEY} stroke="#94a3b8" strokeDasharray="5 3"
                    dot={false} strokeWidth={1.5} isAnimationActive={false} />
                )}
              </ChartInner>
            </ResponsiveContainer>
          </div>
          <div className="flex flex-wrap gap-x-3 gap-y-1 mt-2">
            {parties.map(p => (
              <button key={p} onClick={() => toggle(p)} title="Remove"
                className="inline-flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-300 hover:text-rose-500 group">
                <span className="w-2 h-2 rounded-full" style={{ background: cOf(p) }} />
                {labelOf(p)}<span className="opacity-0 group-hover:opacity-100 text-rose-500">×</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* RIGHT — products near the selected PCI (what sits at this complexity) */}
      <div className="md:col-span-1 lg:col-span-3 min-w-0">
        <div className="panel p-3 h-full">
          <div className="text-[11px] text-slate-400 uppercase tracking-wide">
            {src === 'country' ? `${nameOf(anchor)}’s top ${flowWord} near` : `Top global ${flowWord} near`}
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-amber-500">PCI {fmtPci(selectedPci)}</span>
            <span className="text-xs text-slate-400">{y}</span>
          </div>
          <input type="range" min={-2.5} max={2.5} step={0.01} value={selectedPci}
            onChange={e => setSelectedPci(Number(e.target.value))} className="w-full my-1.5" />
          <div className="text-[11px] text-slate-400 mb-2">
            {src === 'country' ? `${nameOf(anchor)}’s top categories within ±${win.toFixed(2)} PCI`
              : `largest global products within ±${win.toFixed(2)} PCI`} · drag or click the chart
            {selShare != null && <> · selected = {(100 * selShare).toFixed(0)}% of {nameOf(anchor)}’s corridors</>}
            {cov != null && cov < 0.97 && <span className="text-amber-500"> · corridors cover {(100 * cov).toFixed(0)}% of reported total</span>}
          </div>
          {prods.length === 0 ? (
            <div className="text-sm text-slate-400 py-2">No major categories within ±{win.toFixed(2)} of this PCI.</div>
          ) : (
            <div className="space-y-0.5">
              {prods.map(({ hs4, val, pci }) => (
                <div key={hs4} className="relative flex items-center gap-2 py-1 border-b border-slate-100 dark:border-slate-800/60">
                  <div className="absolute inset-y-0 left-0 rounded-sm bg-amber-500/10" style={{ width: `${Math.max(3, (val / maxVal) * 100)}%` }} />
                  <span className="relative font-mono text-xs text-amber-600 dark:text-amber-400 w-10">{fmtPci(pci)}</span>
                  <div className="relative flex-1 min-w-0">
                    <div className="text-sm leading-tight truncate" title={pp?.names?.[hs4]}>{pp?.names?.[hs4] || hs4}</div>
                    <div className="text-[11px] text-slate-400 font-mono">{hs4}</div>
                  </div>
                  <span className="relative font-semibold tabular-nums text-sm whitespace-nowrap">{fmtVal(val)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <p className="lg:col-span-12 text-xs text-slate-400 px-1">
        Bilateral value is one flow — {nameOf(anchor)}’s exports to a partner are that partner’s imports
        from {nameOf(anchor)} — so the “Exports from / Imports to” toggle reads the same matrix two ways.
        Counterparties can be individual countries or <b>region blocs</b> (a region’s curve is the
        value-weighted sum of its member corridors). <b>Share</b> = each counterparty’s % of
        {' '}{nameOf(anchor)}’s {flowWord} at each complexity (stacks toward 100%; the gap is unselected
        {' '}{otherWord} + unallocated flow). The product list shows {nameOf(anchor)}’s own largest
        {' '}{flowWord} categories near the selected PCI (top-50 per year; not corridor-specific).
      </p>
    </div>
  )
}
