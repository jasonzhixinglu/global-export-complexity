import { useMemo } from 'react'
import {
  ResponsiveContainer, LineChart, Line, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine,
} from 'recharts'
import { buildRows, MEASURES } from '../lib/data.js'
import { colorFor, fmtPct, fmtB, fmtPci } from '../lib/format.js'
import { axisColors, tooltipStyle } from '../lib/chartTheme.js'
import { MeasureToggle, Toggle, YearSlider, CountryPicker, PciAxisLegend } from './Controls.jsx'
import { useDarkMode } from '../lib/useDarkMode.jsx'

export default function ExplorerPanel({ data, selected, setSelected, year, setYear, measure, setMeasure }) {
  const { isDark } = useDarkMode()
  const { meta, colorByIso, byIso } = data
  const stackable = MEASURES[measure].stack
  const mode = stackable ? 'stack' : 'line'

  const rows = useMemo(() => buildRows(data, selected, year, measure), [data, selected, year, measure])
  const ac = axisColors(isDark)

  const yfmt = measure === 'share' ? (v) => `${Math.round(v * 100)}%`
    : measure === 'value' ? (v) => `$${v >= 1000 ? (v / 1000).toFixed(1) + 'T' : Math.round(v) + 'B'}`
      : (v) => v.toFixed(2)
  const vfmt = measure === 'share' ? (v) => fmtPct(v, 2)
    : measure === 'value' ? (v) => fmtB(v, 1) : (v) => v?.toFixed(4)

  const toggle = (iso) => setSelected(prev =>
    prev.includes(iso) ? prev.filter(x => x !== iso) : [...prev, iso])

  return (
    <div className="space-y-4">
      <div className="panel p-4 space-y-3">
        <div className="flex flex-wrap items-center gap-3 justify-between">
          <div className="flex flex-wrap items-center gap-3">
            <MeasureToggle value={measure} onChange={setMeasure} measures={MEASURES} />
            {stackable && (
              <Toggle value={mode === 'stack' ? 'stack' : 'line'} onChange={() => {}}
                options={[{ value: 'stack', label: 'Stacked' }]} />
            )}
          </div>
          <span className="text-xs text-slate-500">{MEASURES[measure].unit}</span>
        </div>
        <YearSlider years={meta.years} year={year} onChange={setYear} />
      </div>

      <div className="panel p-4">
        <ResponsiveContainer width="100%" height={440}>
          {mode === 'stack' ? (
            <AreaChart data={rows} margin={{ top: 8, right: 16, bottom: 24, left: 8 }}>
              <CartesianGrid stroke={ac.grid} strokeDasharray="3 3" />
              <XAxis dataKey="pci" type="number" domain={['dataMin', 'dataMax']}
                tick={{ fill: ac.tick, fontSize: 11 }} tickFormatter={fmtPci}
                label={{ value: 'Product Complexity Index (PCI)', position: 'insideBottom', offset: -12, fill: ac.tick, fontSize: 12 }} />
              <YAxis tick={{ fill: ac.tick, fontSize: 11 }} tickFormatter={yfmt} width={52} />
              <ReferenceLine x={0} stroke={ac.grid} />
              <Tooltip contentStyle={tooltipStyle(isDark)} labelFormatter={(p) => `PCI ${fmtPci(p)}`}
                formatter={(v, n) => [vfmt(v), byIso[n]?.name || n]} />
              {selected.map(iso => (
                <Area key={iso} dataKey={iso} stackId="1" stroke={colorFor(colorByIso[iso])}
                  fill={colorFor(colorByIso[iso])} fillOpacity={0.7} strokeWidth={1} isAnimationActive={false} />
              ))}
            </AreaChart>
          ) : (
            <LineChart data={rows} margin={{ top: 8, right: 16, bottom: 24, left: 8 }}>
              <CartesianGrid stroke={ac.grid} strokeDasharray="3 3" />
              <XAxis dataKey="pci" type="number" domain={['dataMin', 'dataMax']}
                tick={{ fill: ac.tick, fontSize: 11 }} tickFormatter={fmtPci}
                label={{ value: 'Product Complexity Index (PCI)', position: 'insideBottom', offset: -12, fill: ac.tick, fontSize: 12 }} />
              <YAxis tick={{ fill: ac.tick, fontSize: 11 }} tickFormatter={yfmt} width={52} />
              <ReferenceLine x={0} stroke={ac.grid} />
              <Tooltip contentStyle={tooltipStyle(isDark)} labelFormatter={(p) => `PCI ${fmtPci(p)}`}
                formatter={(v, n) => [vfmt(v), byIso[n]?.name || n]} />
              {selected.map(iso => (
                <Line key={iso} dataKey={iso} stroke={colorFor(colorByIso[iso])}
                  dot={false} strokeWidth={2} isAnimationActive={false} />
              ))}
            </LineChart>
          )}
        </ResponsiveContainer>
        <div className="mt-2"><PciAxisLegend anchors={data.anchors} /></div>
      </div>

      <div className="panel p-4">
        <div className="label mb-2">Countries — click to add/remove ({selected.length} selected)</div>
        <CountryPicker countries={meta.countries} regionsOrder={meta.regionsOrder}
          selected={selected} onToggle={toggle} colorByIso={colorByIso} />
      </div>
    </div>
  )
}
