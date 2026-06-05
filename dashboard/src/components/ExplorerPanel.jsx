import { useMemo, useState } from 'react'
import {
  ResponsiveContainer, LineChart, Line, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine,
} from 'recharts'
import { buildRows, MEASURES } from '../lib/data.js'
import { colorFor, fmtPct, fmtB, fmtPci } from '../lib/format.js'
import { axisColors, tooltipStyle } from '../lib/chartTheme.js'
import { MeasureToggle, Toggle, YearStepper, CountryPicker, PciAxisLegend } from './Controls.jsx'
import { useDarkMode } from '../lib/useDarkMode.jsx'

export default function ExplorerPanel({ data, selected, setSelected, year, setYear, measure, setMeasure }) {
  const { isDark } = useDarkMode()
  const { meta, colorByIso, byIso } = data
  const stackable = MEASURES[measure].stack
  const [display, setDisplay] = useState('stack')
  const [selectedPci, setSelectedPci] = useState(1.0)
  const mode = stackable && display === 'stack' ? 'stack' : 'line'

  const rows = useMemo(() => buildRows(data, selected, year, measure), [data, selected, year, measure])
  const ac = axisColors(isDark)

  // PCI drill-down: top global products near the selected complexity (current year)
  const pp = data.pciProducts
  const bin = pp ? Math.max(0, Math.min(pp.centers.length - 1, Math.floor((selectedPci - pp.lo) / pp.binWidth))) : 0
  const prods = pp ? (pp.top[String(year)]?.[bin] || []) : []
  const onPick = (e) => { if (e && e.activeLabel != null) setSelectedPci(Number(e.activeLabel)) }

  const yfmt = measure === 'share' ? (v) => `${Math.round(v * 100)}%`
    : measure === 'value' ? (v) => `$${v >= 1000 ? (v / 1000).toFixed(1) + 'T' : Math.round(v) + 'B'}`
      : (v) => v.toFixed(2)
  const vfmt = measure === 'share' ? (v) => fmtPct(v, 2)
    : measure === 'value' ? (v) => fmtB(v, 1) : (v) => v?.toFixed(4)

  const toggle = (iso) => setSelected(prev =>
    prev.includes(iso) ? prev.filter(x => x !== iso) : [...prev, iso])

  const ChartInner = mode === 'stack' ? AreaChart : LineChart
  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-3">
      {/* LEFT — controls: year + countries */}
      <div className="lg:col-span-3 space-y-3">
        <div className="panel p-3 space-y-2">
          <div className="label">Year</div>
          <YearStepper years={meta.years} year={year} onChange={setYear} />
        </div>
        <div className="panel p-3">
          <div className="label mb-2">Countries · {selected.length} selected</div>
          <CountryPicker countries={meta.countries} regionsOrder={meta.regionsOrder}
            selected={selected} onToggle={toggle} colorByIso={colorByIso} />
        </div>
      </div>

      {/* MIDDLE — distribution chart */}
      <div className="lg:col-span-6">
        <div className="panel p-3">
          <div className="flex flex-wrap items-center gap-3 justify-between mb-2">
            <MeasureToggle value={measure} onChange={setMeasure} measures={MEASURES} />
            <div className="flex items-center gap-3">
              {stackable && (
                <Toggle value={display} onChange={setDisplay}
                  options={[{ value: 'stack', label: 'Stacked' }, { value: 'line', label: 'Lines' }]} />
              )}
              <span className="text-xs text-slate-500">{MEASURES[measure].unit} · {year}</span>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={470}>
            <ChartInner data={rows} margin={{ top: 8, right: 12, bottom: 24, left: 4 }} onClick={onPick}>
              <CartesianGrid stroke={ac.grid} strokeDasharray="2 2" />
              <XAxis dataKey="pci" type="number" domain={['dataMin', 'dataMax']} tickCount={11}
                tick={{ fill: ac.tick, fontSize: 10 }} tickFormatter={fmtPci}
                label={{ value: 'Product Complexity Index (PCI)', position: 'insideBottom', offset: -12, fill: ac.tick, fontSize: 11 }} />
              <YAxis tick={{ fill: ac.tick, fontSize: 10 }} tickFormatter={yfmt} width={46} tickCount={9} />
              <ReferenceLine x={0} stroke={ac.grid} />
              <ReferenceLine x={selectedPci} stroke="#f59e0b" strokeWidth={1.5} strokeDasharray="4 2"
                label={{ value: fmtPci(selectedPci), position: 'top', fill: '#f59e0b', fontSize: 11 }} />
              <Tooltip contentStyle={tooltipStyle(isDark)} labelFormatter={(p) => `PCI ${fmtPci(p)}`}
                formatter={(v, n) => [vfmt(v), byIso[n]?.name || n]} />
              {mode === 'stack'
                ? selected.map(iso => (
                  <Area key={iso} dataKey={iso} stackId="1" stroke={colorFor(colorByIso[iso])}
                    fill={colorFor(colorByIso[iso])} fillOpacity={0.7} strokeWidth={1} isAnimationActive={false} />
                ))
                : selected.map(iso => (
                  <Line key={iso} dataKey={iso} stroke={colorFor(colorByIso[iso])}
                    dot={false} strokeWidth={2} isAnimationActive={false} />
                ))}
            </ChartInner>
          </ResponsiveContainer>
          <div className="mt-2"><PciAxisLegend anchors={data.anchors} /></div>
        </div>
      </div>

      {/* RIGHT — top products near the selected PCI */}
      <div className="lg:col-span-3">
        <div className="panel p-3 h-full">
          <div className="text-xs text-slate-400 uppercase tracking-wide">Top global exports near</div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-amber-500">PCI {fmtPci(selectedPci)}</span>
            <span className="text-xs text-slate-400">{year}</span>
          </div>
          <div className="text-[11px] text-slate-400 mb-2">click the chart to change the complexity level</div>
          {prods.length === 0 ? (
            <div className="text-sm text-slate-400 py-2">No products in this bin.</div>
          ) : (
            <div className="space-y-0.5">
              {prods.map(([hs4, val, pci], i) => (
                <div key={hs4} className="flex items-center gap-2 py-1 border-b border-slate-100 dark:border-slate-800/60">
                  <span className="text-slate-400 w-4 text-right text-xs">{i + 1}</span>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm leading-tight truncate" title={pp?.names?.[hs4]}>{pp?.names?.[hs4] || hs4}</div>
                    <div className="text-[11px] text-slate-400 font-mono">{hs4} · PCI {fmtPci(pci)}</div>
                  </div>
                  <span className="font-semibold tabular-nums text-sm whitespace-nowrap">{fmtB(val, 1)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
