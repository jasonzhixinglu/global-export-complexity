import { useMemo, useState } from 'react'
import {
  ResponsiveContainer, ComposedChart, Line, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine,
} from 'recharts'
import { buildRows, MEASURES } from '../lib/data.js'
import { colorFor, fmtPct, fmtB, fmtPci } from '../lib/format.js'
import { axisColors, tooltipStyle } from '../lib/chartTheme.js'
import { MeasureToggle, Toggle, YearSlider, CountryPicker, PciAxisLegend } from './Controls.jsx'
import { useDarkMode } from '../lib/useDarkMode.jsx'

function Swatch({ color }) {
  return <span className="inline-block w-2.5 h-2.5 rounded-full" style={{ background: color }} />
}

export default function ExplorerPanel({ data, selected, setSelected, year, setYear, measure, setMeasure }) {
  const { isDark } = useDarkMode()
  const { meta, colorByIso, byIso } = data
  const stackable = MEASURES[measure].stack
  const [display, setDisplay] = useState('stack')
  const mode = stackable && display === 'stack' ? 'stack' : 'line'

  const rows = useMemo(() => buildRows(data, selected, year, measure), [data, selected, year, measure])
  const ac = axisColors(isDark)

  const yfmt = measure === 'share' ? (v) => `${Math.round(v * 100)}%`
    : measure === 'value' ? (v) => `$${v >= 1000 ? (v / 1000).toFixed(1) + 'T' : Math.round(v) + 'B'}`
      : (v) => v.toFixed(2)
  const vfmt = measure === 'share' ? (v) => fmtPct(v, 2)
    : measure === 'value' ? (v) => fmtB(v, 1) : (v) => v?.toFixed(4)

  const toggle = (iso) => setSelected(prev =>
    prev.includes(iso) ? prev.filter(x => x !== iso) : [...prev, iso])

  const title = `${MEASURES[measure].label} across complexity — ${year}${mode === 'stack' ? ' · cumulative' : ''}`

  return (
    <div className="space-y-4">
      <div className="panel p-4 space-y-3.5">
        <div className="flex flex-wrap items-center gap-x-4 gap-y-3 justify-between">
          <div className="flex flex-wrap items-center gap-3">
            <MeasureToggle value={measure} onChange={setMeasure} measures={MEASURES} />
            {stackable && (
              <Toggle value={display} onChange={setDisplay}
                options={[{ value: 'stack', label: 'Stacked' }, { value: 'line', label: 'Lines' }]} />
            )}
          </div>
          <span className="text-xs text-slate-400">{MEASURES[measure].unit}</span>
        </div>
        <YearSlider years={meta.years} year={year} onChange={setYear} />
      </div>

      <div className="panel p-5">
        <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
          <h2 className="panel-title">{title}</h2>
          <div className="flex flex-wrap gap-x-3 gap-y-1">
            {selected.map(iso => (
              <span key={iso} className="inline-flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-300">
                <Swatch color={colorFor(colorByIso[iso])} />{byIso[iso]?.name || iso}
              </span>
            ))}
          </div>
        </div>
        <ResponsiveContainer width="100%" height={430}>
          <ComposedChart data={rows} margin={{ top: 8, right: 20, bottom: 24, left: 8 }}>
            <defs>
              {selected.map(iso => {
                const c = colorFor(colorByIso[iso])
                return (
                  <linearGradient key={iso} id={`grad-${iso}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={c} stopOpacity={mode === 'stack' ? 0.85 : 0.35} />
                    <stop offset="100%" stopColor={c} stopOpacity={mode === 'stack' ? 0.5 : 0.02} />
                  </linearGradient>
                )
              })}
            </defs>
            <CartesianGrid stroke={ac.grid} strokeDasharray="2 4" vertical={false} />
            <XAxis dataKey="pci" type="number" domain={['dataMin', 'dataMax']} tickLine={false}
              axisLine={{ stroke: ac.grid }} tick={{ fill: ac.tick, fontSize: 11 }} tickFormatter={fmtPci}
              label={{ value: 'Product Complexity Index (PCI)', position: 'insideBottom', offset: -12, fill: ac.tick, fontSize: 12 }} />
            <YAxis tick={{ fill: ac.tick, fontSize: 11 }} tickFormatter={yfmt} width={52}
              tickLine={false} axisLine={false} />
            <ReferenceLine x={0} stroke={ac.grid} strokeDasharray="3 3" />
            <Tooltip contentStyle={tooltipStyle(isDark)} cursor={{ stroke: ac.grid }}
              labelFormatter={(p) => `PCI ${fmtPci(p)}`}
              formatter={(v, n) => [vfmt(v), byIso[n]?.name || n]} />
            {selected.map(iso => mode === 'stack' ? (
              <Area key={iso} type="monotone" dataKey={iso} stackId="1" stroke={colorFor(colorByIso[iso])}
                fill={`url(#grad-${iso})`} strokeWidth={1.25} isAnimationActive={false} />
            ) : (
              <Area key={iso} type="monotone" dataKey={iso} stroke={colorFor(colorByIso[iso])}
                fill={`url(#grad-${iso})`} strokeWidth={2} isAnimationActive={false} />
            ))}
          </ComposedChart>
        </ResponsiveContainer>
        <div className="mt-3 pt-3 border-t border-slate-100 dark:border-slate-800"><PciAxisLegend anchors={data.anchors} /></div>
      </div>

      <div className="panel p-5">
        <div className="label mb-2.5">Countries — click to add or remove · {selected.length} selected</div>
        <CountryPicker countries={meta.countries} regionsOrder={meta.regionsOrder}
          selected={selected} onToggle={toggle} colorByIso={colorByIso} />
      </div>
    </div>
  )
}
