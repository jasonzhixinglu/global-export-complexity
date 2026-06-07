import { useEffect, useMemo, useState } from 'react'
import {
  ResponsiveContainer, LineChart, Line, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine,
} from 'recharts'
import {
  buildMixtureRows, corridorOf, corridorCounterparties, CORRIDOR_MEASURES,
} from '../lib/data.js'
import { colorFor, fmtB, fmtPci } from '../lib/format.js'
import { axisColors, tooltipStyle } from '../lib/chartTheme.js'
import { Toggle, YearStepper, CountryPicker } from './Controls.jsx'
import { useDarkMode } from '../lib/useDarkMode.jsx'

const ANCHOR_KEY = '__anchor__'

export default function BilateralPanel({ data, year, setYear }) {
  const { isDark } = useDarkMode()
  const { meta, byIso, gmmBilateral: bil } = data
  const [role, setRole] = useState('origin')          // 'origin' = exports from; 'dest' = imports to
  const [anchor, setAnchor] = useState('CHN')
  const [parties, setParties] = useState([])
  const [measure, setMeasure] = useState('value')
  const [level, setLevel] = useState(meta.defaultLevel || 'med')
  const [display, setDisplay] = useState('stack')
  const [q, setQ] = useState('')
  const ac = axisColors(isDark)

  if (!bil) return <div className="panel p-6 text-sm text-slate-400">Bilateral corridor data not available.</div>

  const y = String(Math.min(bil.years[bil.years.length - 1], Math.max(bil.years[0], year)))
  const nameOf = (iso) => iso === 'ROW' ? 'Rest of world' : (byIso[iso]?.name || iso)
  const cflow = role === 'origin' ? 'export' : 'import'
  const otherWord = role === 'origin' ? 'destinations' : 'origins'

  // counterparties available for this anchor/year/role, ranked by corridor value
  const ranked = useMemo(() => corridorCounterparties(data, anchor, Number(y), role),
    [data, anchor, y, role])

  // when the anchor or perspective changes, default to its top counterparties (+ ROW)
  useEffect(() => {
    const top = ranked.slice(0, 4).map(d => d.iso)
    if (ranked.some(d => d.iso === 'ROW') && !top.includes('ROW')) top.push('ROW')
    setParties(top)
  }, [anchor, role])  // eslint-disable-line react-hooks/exhaustive-deps

  const colorOf = useMemo(() => {
    const m = {}; parties.forEach((p, i) => { m[p] = colorFor(i) }); return m
  }, [parties])
  const cOf = (iso) => colorOf[iso] || '#94a3b8'

  const stack = measure === 'value' && display === 'stack'

  // chart series: each selected corridor + the anchor's own country-level distribution (reference)
  const rows = useMemo(() => {
    const series = parties.map(p => ({ name: p, ...corridorOf(data, anchor, p, Number(y), role) }))
    const aParams = data.gmm?.mix?.[cflow]?.[anchor]?.[y]
    const aTotal = data.series?.totalB?.[cflow]?.[anchor]?.[y]
    series.push({ name: ANCHOR_KEY, params: aParams || null, total: aTotal ?? null })
    return buildMixtureRows(data, series, measure, level)
  }, [data, parties, anchor, y, role, measure, level])

  // coverage caption: selected share of corridor total, and corridor coverage of reported total
  const totalCorr = ranked.reduce((s, d) => s + d.valueB, 0)
  const selSum = parties.reduce((s, p) => s + (corridorOf(data, anchor, p, Number(y), role).total || 0), 0)
  const countryTot = data.series?.totalB?.[cflow]?.[anchor]?.[y]
  const selShare = totalCorr ? selSum / totalCorr : null
  const cov = countryTot ? totalCorr / countryTot : null

  const yfmt = measure === 'value' ? (v) => `$${v >= 1000 ? (v / 1000).toFixed(1) + 'T' : Math.round(v) + 'B'}` : (v) => v.toFixed(2)
  const vfmt = measure === 'value' ? (v) => fmtB(v, 1) : (v) => v?.toFixed(4)

  const toggle = (iso) => setParties(prev => prev.includes(iso) ? prev.filter(x => x !== iso) : [...prev, iso])
  const toggleRegion = (isos, addAll) => setParties(prev =>
    addAll ? [...new Set([...prev, ...isos])] : prev.filter(x => !isos.includes(x)))

  // country list for the picker = the bilateral blocs (top-N + ROW), mapped to name/region
  const corrCountries = bil.blocs.map(b => b === 'ROW'
    ? { iso3: 'ROW', name: 'Rest of world', region: 'Rest of world' }
    : (byIso[b] || { iso3: b, name: b, region: 'Other' }))
  const regionsOrder = [...meta.regionsOrder, 'Rest of world']

  const ChartInner = stack ? AreaChart : LineChart
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-12 gap-3">
      {/* LEFT — perspective, anchor, counterparties */}
      <div className="md:col-span-1 lg:col-span-3 min-w-0">
        <div className="panel p-3 h-full flex flex-col gap-3">
          <div>
            <div className="label mb-1">Perspective</div>
            <Toggle value={role} onChange={setRole}
              options={[{ value: 'origin', label: 'Exports from' }, { value: 'dest', label: 'Imports to' }]} />
          </div>
          <div>
            <div className="label mb-1">{role === 'origin' ? 'Exporter' : 'Importer'}</div>
            <select value={anchor} onChange={e => setAnchor(e.target.value)}
              className="w-full bg-transparent border border-slate-300 dark:border-slate-600 rounded px-2 py-1 text-sm">
              {bil.blocs.map(b => <option key={b} value={b}>{nameOf(b)}</option>)}
            </select>
          </div>
          <div className="flex items-center justify-between">
            <span className="label">Year</span>
            <YearStepper years={bil.years} year={Number(y)} onChange={setYear} />
          </div>
          <div className="border-t border-slate-200 dark:border-slate-800 pt-2 flex flex-col flex-1 min-h-0 gap-2">
            <div className="flex items-center justify-between">
              <div className="label">{otherWord} · {parties.length}</div>
              <button onClick={() => setParties([])} disabled={!parties.length}
                className="text-[11px] text-slate-400 hover:text-rose-500 disabled:opacity-40">Clear</button>
            </div>
            <input value={q} onChange={e => setQ(e.target.value)} placeholder={`Filter ${otherWord}…`}
              className="w-full bg-transparent border border-slate-300 dark:border-slate-600 rounded px-2 py-1 text-sm placeholder:text-slate-400 focus:outline-none focus:border-indigo-400" />
            <div className="flex-1 min-h-0 overflow-y-auto pr-1 -mr-1 max-h-[50vh] lg:max-h-none">
              <CountryPicker countries={corrCountries} regionsOrder={regionsOrder}
                selected={parties} onToggle={toggle} onToggleRegion={toggleRegion} colorOf={cOf} query={q} />
            </div>
          </div>
        </div>
      </div>

      {/* MIDDLE — corridor distributions */}
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
              {measure === 'value' && (
                <Toggle value={display} onChange={setDisplay}
                  options={[{ value: 'stack', label: 'Stacked' }, { value: 'lines', label: 'Lines' }]} />
              )}
            </div>
          </div>
          <div className="text-[11px] text-slate-400 mb-1">
            {role === 'origin' ? `${nameOf(anchor)} → ` : `→ ${nameOf(anchor)}`}{otherWord}, {y} ·
            {' '}dashed = {nameOf(anchor)}’s total {cflow} distribution
          </div>
          <ResponsiveContainer width="100%" height={430}>
            <ChartInner data={rows} margin={{ top: 8, right: 12, bottom: 24, left: 4 }}>
              <CartesianGrid stroke={ac.grid} strokeDasharray="2 2" />
              <XAxis dataKey="pci" type="number" domain={['dataMin', 'dataMax']} tickCount={11}
                tick={{ fill: ac.tick, fontSize: 10 }} tickFormatter={fmtPci}
                label={{ value: 'Product Complexity Index (PCI)', position: 'insideBottom', offset: -12, fill: ac.tick, fontSize: 11 }} />
              <YAxis tick={{ fill: ac.tick, fontSize: 10 }} tickFormatter={yfmt} width={46} />
              <ReferenceLine x={0} stroke={ac.grid} />
              <Tooltip contentStyle={tooltipStyle(isDark)} labelFormatter={(p) => `PCI ${fmtPci(p)}`}
                formatter={(v, n) => [vfmt(v), n === ANCHOR_KEY ? `${nameOf(anchor)} (total)` : nameOf(n)]} />
              {stack
                ? parties.map(p => (
                  <Area key={p} type="monotone" dataKey={p} stackId="1" stroke={cOf(p)}
                    fill={cOf(p)} fillOpacity={0.7} strokeWidth={1} isAnimationActive={false} />
                ))
                : parties.map(p => (
                  <Line key={p} type="monotone" dataKey={p} stroke={cOf(p)}
                    dot={false} strokeWidth={2} isAnimationActive={false} />
                ))}
              <Line type="monotone" dataKey={ANCHOR_KEY} stroke="#94a3b8" strokeDasharray="5 3"
                dot={false} strokeWidth={1.5} isAnimationActive={false} />
            </ChartInner>
          </ResponsiveContainer>
          <div className="flex flex-wrap gap-x-3 gap-y-1 mt-2">
            {parties.map(p => (
              <button key={p} onClick={() => toggle(p)} title="Remove"
                className="inline-flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-300 hover:text-rose-500 group">
                <span className="w-2 h-2 rounded-full" style={{ background: cOf(p) }} />
                {nameOf(p)}<span className="opacity-0 group-hover:opacity-100 text-rose-500">×</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* RIGHT — ranked counterparties by corridor value */}
      <div className="md:col-span-1 lg:col-span-3 min-w-0">
        <div className="panel p-3 h-full flex flex-col">
          <div className="text-[11px] text-slate-400 uppercase tracking-wide">
            Top {otherWord} · {nameOf(anchor)} · {y}
          </div>
          {selShare != null && (
            <div className="text-[11px] text-slate-400 mt-1 mb-2">
              selected = {(100 * selShare).toFixed(0)}% of these corridors
              {cov != null && cov < 0.97 && (
                <span className="text-amber-500"> · corridors cover {(100 * cov).toFixed(0)}% of reported total (rest unallocated)</span>
              )}
            </div>
          )}
          <div className="space-y-0.5 overflow-y-auto pr-1 -mr-1 flex-1 min-h-0 max-h-[55vh] lg:max-h-none mt-1">
            {ranked.slice(0, 20).map(({ iso, valueB }) => {
              const on = parties.includes(iso)
              const max = ranked[0]?.valueB || 1
              return (
                <button key={iso} onClick={() => toggle(iso)}
                  className="relative w-full flex items-center gap-2 py-1 text-left border-b border-slate-100 dark:border-slate-800/60">
                  <span className="absolute inset-y-0 left-0 rounded-sm" style={{ width: `${Math.max(3, (valueB / max) * 100)}%`, background: on ? cOf(iso) + '33' : '#94a3b822' }} />
                  <span className="relative w-2 h-2 rounded-full shrink-0" style={{ background: on ? cOf(iso) : 'transparent', border: on ? 'none' : '1px solid #94a3b8' }} />
                  <span className="relative flex-1 min-w-0 truncate text-sm">{nameOf(iso)}</span>
                  <span className="relative tabular-nums text-xs text-slate-500">{fmtB(valueB, 1)}</span>
                </button>
              )
            })}
          </div>
        </div>
      </div>

      <p className="lg:col-span-12 text-xs text-slate-400 px-1">
        Bilateral value is one flow — {nameOf(anchor)}’s exports to a partner are that partner’s imports
        from {nameOf(anchor)} — so the “Exports from / Imports to” toggle reads the same matrix two ways.
        Each curve is a Gaussian-mixture reconstruction of the corridor’s value distribution over PCI;
        stacked Value should track the dashed country total (the recomposition check). Corridors of
        commodity exporters may under-sum their reported total when exports route to unallocated partners.
      </p>
    </div>
  )
}
