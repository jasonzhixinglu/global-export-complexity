import { useMemo, useState } from 'react'
import {
  ResponsiveContainer, LineChart, Line, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine,
} from 'recharts'
import { buildRows, MEASURES } from '../lib/data.js'
import { colorFor, fmtPct, fmtB, fmtPci } from '../lib/format.js'
import { axisColors, tooltipStyle } from '../lib/chartTheme.js'
import { MeasureToggle, Toggle, YearStepper, CountryPicker } from './Controls.jsx'
import { useDarkMode } from '../lib/useDarkMode.jsx'

export default function ExplorerPanel({ data, selected, setSelected, year, setYear, measure, setMeasure }) {
  const { isDark } = useDarkMode()
  const { meta, byIso } = data
  const stackable = MEASURES[measure].stack
  const [display, setDisplay] = useState('stack')
  const [selectedPci, setSelectedPci] = useState(1.0)
  const [q, setQ] = useState('')
  const mode = stackable && display === 'stack' ? 'stack' : 'line'

  const rows = useMemo(() => buildRows(data, selected, year, measure), [data, selected, year, measure])
  const ac = axisColors(isDark)

  // colour by position in the current selection (stable, no global-index collisions)
  const colorOf = useMemo(() => {
    const m = {}; selected.forEach((iso, i) => { m[iso] = colorFor(i) }); return m
  }, [selected])
  const cOf = (iso) => colorOf[iso] || '#94a3b8'

  // PCI drill-down: within a window around the selected PCI, the 10 LARGEST products by
  // export value (continuous window, so the list shifts as you move the selector).
  const PCI_WINDOW = 0.02
  const pp = data.pciProducts
  // start at ±0.02; if fewer than 10 products fall in the window, widen until it has 10
  // (so sparse high-PCI regions still fill), then show the 10 largest by value.
  const { prods, win } = useMemo(() => {
    const list = pp?.byYear?.[String(year)] || []
    if (!list.length) return { prods: [], win: PCI_WINDOW }
    let w = PCI_WINDOW
    let cand = list.filter(p => Math.abs(p[1] - selectedPci) <= w)
    while (cand.length < 10 && w < 1.5) { w += 0.02; cand = list.filter(p => Math.abs(p[1] - selectedPci) <= w) }
    const prods = cand.sort((a, b) => b[2] - a[2]).slice(0, 10).map(p => ({ hs4: p[0], pci: p[1], val: p[2] }))
    return { prods, win: w }
  }, [pp, year, selectedPci])
  const maxVal = prods.length ? Math.max(...prods.map(p => p.val)) : 1
  const onPick = (e) => { if (e && e.activeLabel != null) setSelectedPci(Number(e.activeLabel)) }

  const yfmt = measure === 'share' ? (v) => `${Math.round(v * 100)}%`
    : measure === 'value' ? (v) => `$${v >= 1000 ? (v / 1000).toFixed(1) + 'T' : Math.round(v) + 'B'}`
      : (v) => v.toFixed(2)
  const vfmt = measure === 'share' ? (v) => fmtPct(v, 2)
    : measure === 'value' ? (v) => fmtB(v, 1) : (v) => v?.toFixed(4)

  const toggle = (iso) => setSelected(prev =>
    prev.includes(iso) ? prev.filter(x => x !== iso) : [...prev, iso])
  const toggleRegion = (isos, addAll) => setSelected(prev =>
    addAll ? [...new Set([...prev, ...isos])] : prev.filter(x => !isos.includes(x)))

  const ChartInner = mode === 'stack' ? AreaChart : LineChart
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-12 gap-3">
      {/* LEFT — controls: year + countries (one panel) */}
      <div className="md:col-span-1 lg:col-span-3">
        <div className="panel p-3 h-full flex flex-col gap-3">
          <div className="flex items-center justify-between gap-2">
            <span className="label">Year</span>
            <YearStepper years={meta.years} year={year} onChange={setYear} />
          </div>
          <div className="border-t border-slate-200 dark:border-slate-800 pt-3 flex flex-col flex-1 min-h-0 gap-2">
            <div className="flex items-center justify-between">
              <div className="label">Countries · {selected.length}</div>
              <button onClick={() => setSelected([])} disabled={!selected.length}
                className="text-[11px] text-slate-400 hover:text-rose-500 disabled:opacity-40">Clear</button>
            </div>
            <input value={q} onChange={e => setQ(e.target.value)} placeholder="Filter countries…"
              className="w-full bg-transparent border border-slate-300 dark:border-slate-600 rounded px-2 py-1 text-sm placeholder:text-slate-400 focus:outline-none focus:border-indigo-400" />
            <div className="flex-1 min-h-0 overflow-y-auto pr-1 -mr-1 max-h-[60vh] lg:max-h-none">
              <CountryPicker countries={meta.countries} regionsOrder={meta.regionsOrder}
                selected={selected} onToggle={toggle} onToggleRegion={toggleRegion}
                colorOf={cOf} query={q} />
            </div>
          </div>
        </div>
      </div>

      {/* MIDDLE — distribution chart */}
      <div className="md:col-span-2 lg:col-span-6 md:order-last lg:order-none">
        <div className="panel p-3 h-full">
          <div className="flex flex-wrap items-center gap-3 justify-between mb-2">
            <MeasureToggle value={measure} onChange={setMeasure} measures={MEASURES} />
            <div className="flex items-center gap-3">
              {stackable && (
                <Toggle value={display} onChange={setDisplay}
                  options={[{ value: 'stack', label: 'Stacked' }, { value: 'line', label: 'Lines' }]} />
              )}
              <span className="text-[11px] text-amber-500/90 inline-flex items-center gap-1">
                <span className="inline-block w-3 border-t border-dashed border-amber-500" /> click to inspect
              </span>
            </div>
          </div>
          <div className="cursor-crosshair">
            <ResponsiveContainer width="100%" height={460}>
              <ChartInner data={rows} margin={{ top: 8, right: 12, bottom: 24, left: 4 }} onClick={onPick}>
                <CartesianGrid stroke={ac.grid} strokeDasharray="2 2" />
                <XAxis dataKey="pci" type="number" domain={['dataMin', 'dataMax']} tickCount={11}
                  tick={{ fill: ac.tick, fontSize: 10 }} tickFormatter={fmtPci}
                  label={{ value: 'Product Complexity Index (PCI)', position: 'insideBottom', offset: -12, fill: ac.tick, fontSize: 11 }} />
                <YAxis tick={{ fill: ac.tick, fontSize: 10 }} tickFormatter={yfmt} width={46} tickCount={9}
                  domain={measure === 'share' ? [0, 1] : [0, 'auto']} allowDataOverflow={measure === 'share'} />
                <ReferenceLine x={0} stroke={ac.grid} />
                <ReferenceLine x={selectedPci} stroke="#f59e0b" strokeWidth={1.5} strokeDasharray="4 2" />
                <Tooltip contentStyle={tooltipStyle(isDark)} labelFormatter={(p) => `PCI ${fmtPci(p)}`}
                  formatter={(v, n) => [vfmt(v), byIso[n]?.name || n]} />
                {mode === 'stack'
                  ? selected.map(iso => (
                    <Area key={iso} dataKey={iso} stackId="1" stroke={cOf(iso)}
                      fill={cOf(iso)} fillOpacity={0.7} strokeWidth={1} isAnimationActive={false} />
                  ))
                  : selected.map(iso => (
                    <Line key={iso} dataKey={iso} stroke={cOf(iso)}
                      dot={false} strokeWidth={2} isAnimationActive={false} />
                  ))}
              </ChartInner>
            </ResponsiveContainer>
          </div>
          {/* legend: colour ↔ country, click to remove */}
          <div className="flex flex-wrap gap-x-3 gap-y-1 mt-2">
            {selected.map(iso => (
              <button key={iso} onClick={() => toggle(iso)} title="Remove"
                className="inline-flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-300 hover:text-rose-500 group">
                <span className="w-2 h-2 rounded-full" style={{ background: cOf(iso) }} />
                {byIso[iso]?.name || iso}
                <span className="opacity-0 group-hover:opacity-100 text-rose-500">×</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* RIGHT — top products near the selected PCI */}
      <div className="md:col-span-1 lg:col-span-3">
        <div className="panel p-3 h-full">
          <div className="text-[11px] text-slate-400 uppercase tracking-wide">Top global exports near</div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-amber-500">PCI {fmtPci(selectedPci)}</span>
            <span className="text-xs text-slate-400">{year}</span>
          </div>
          <input type="range" min={-2.5} max={2.5} step={0.01} value={selectedPci}
            onChange={e => setSelectedPci(Number(e.target.value))} className="w-full my-1.5" />
          <div className="text-[11px] text-slate-400 mb-2">largest exports within ±{win.toFixed(2)} PCI · drag the slider or click the chart</div>
          {prods.length === 0 ? (
            <div className="text-sm text-slate-400 py-2">No products in this bin.</div>
          ) : (
            <div className="space-y-0.5">
              {prods.map(({ hs4, val, pci }) => (
                <div key={hs4} className="relative flex items-center gap-2 py-1 border-b border-slate-100 dark:border-slate-800/60">
                  <div className="absolute inset-y-0 left-0 rounded-sm bg-amber-500/10"
                    style={{ width: `${Math.max(3, (val / maxVal) * 100)}%` }} />
                  <span className="relative font-mono text-xs text-amber-600 dark:text-amber-400 w-10">{fmtPci(pci)}</span>
                  <div className="relative flex-1 min-w-0">
                    <div className="text-sm leading-tight truncate" title={pp?.names?.[hs4]}>{pp?.names?.[hs4] || hs4}</div>
                    <div className="text-[11px] text-slate-400 font-mono">{hs4}</div>
                  </div>
                  <span className="relative font-semibold tabular-nums text-sm whitespace-nowrap">{fmtB(val, 1)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
