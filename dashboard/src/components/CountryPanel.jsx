import { useMemo, useState } from 'react'
import {
  ResponsiveContainer, AreaChart, Area, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine,
} from 'recharts'
import { buildRows, MEASURES } from '../lib/data.js'
import { colorFor, fmtPct, fmtB, fmtPci } from '../lib/format.js'
import { axisColors, tooltipStyle } from '../lib/chartTheme.js'
import { MeasureToggle, YearSlider } from './Controls.jsx'
import { useDarkMode } from '../lib/useDarkMode.jsx'

function meanPci(data, iso, year) {
  const { meta, series } = data
  const g = meta.kdeGrid
  const dx = g.length > 1 ? g[1] - g[0] : 1
  const dens = series.density[iso]?.[String(year)]
  if (!dens) return null
  let m = 0, tot = 0
  for (let i = 0; i < g.length; i++) { m += g[i] * (dens[i] || 0) * dx; tot += (dens[i] || 0) * dx }
  return tot ? m / tot : null
}

function Stat({ label, value, sub }) {
  return (
    <div className="card p-3">
      <div className="label">{label}</div>
      <div className="text-xl font-semibold mt-1">{value}</div>
      {sub && <div className="text-xs text-slate-500 mt-0.5">{sub}</div>}
    </div>
  )
}

export default function CountryPanel({ data, year, measure }) {
  const { isDark } = useDarkMode()
  const { meta, byIso, colorByIso } = data
  const [iso, setIso] = useState(meta.countries[0]?.iso3 || 'CHN')
  const ac = axisColors(isDark)
  const color = colorFor(colorByIso[iso])

  const rows = useMemo(() => buildRows(data, [iso], year, measure), [data, iso, year, measure])
  const total = data.series.totalB[iso]?.[String(year)]
  const mpci = meanPci(data, iso, year)
  const trend = useMemo(() => meta.years.map(yr => ({
    year: yr, total: data.series.totalB[iso]?.[String(yr)], mpci: meanPci(data, iso, yr),
  })), [data, iso, meta.years])

  const yfmt = measure === 'share' ? (v) => `${Math.round(v * 100)}%`
    : measure === 'value' ? (v) => `$${Math.round(v)}B` : (v) => v.toFixed(2)
  const vfmt = measure === 'share' ? (v) => fmtPct(v, 2) : measure === 'value' ? (v) => fmtB(v, 1) : (v) => v?.toFixed(4)

  return (
    <div className="space-y-4">
      <div className="panel p-3 flex flex-wrap items-center gap-2">
        <span className="label">Country</span>
        <select value={iso} onChange={e => setIso(e.target.value)}
          className="bg-transparent border border-slate-300 dark:border-slate-600 rounded px-3 py-1.5 text-sm">
          {meta.countries.map(c => <option key={c.iso3} value={c.iso3}>{c.name} ({c.iso3})</option>)}
        </select>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        <Stat label="Total exports" value={fmtB(total, 1)} sub={`${year}`} />
        <Stat label="Avg complexity (value-wtd)" value={fmtPci(mpci)} sub="mean PCI of export $" />
        <Stat label="Tracked rank by value" value={`#${[...meta.countries].map(c => c.iso3)
          .sort((a, b) => (data.series.totalB[b]?.[String(year)] || 0) - (data.series.totalB[a]?.[String(year)] || 0))
          .indexOf(iso) + 1}`} sub={`of ${meta.countries.length}`} />
      </div>

      <div className="panel p-4">
        <div className="label mb-2">{byIso[iso].name} — {MEASURES[measure].label} across complexity, {year}</div>
        <ResponsiveContainer width="100%" height={340}>
          <AreaChart data={rows} margin={{ top: 8, right: 16, bottom: 24, left: 8 }}>
            <CartesianGrid stroke={ac.grid} strokeDasharray="2 2" />
            <XAxis dataKey="pci" type="number" domain={['dataMin', 'dataMax']} tickFormatter={fmtPci} tickCount={11}
              tick={{ fill: ac.tick, fontSize: 10 }}
              label={{ value: 'PCI', position: 'insideBottom', offset: -12, fill: ac.tick, fontSize: 11 }} />
            <YAxis tick={{ fill: ac.tick, fontSize: 10 }} tickFormatter={yfmt} width={48} tickCount={9} />
            <ReferenceLine x={0} stroke={ac.grid} />
            <Tooltip contentStyle={tooltipStyle(isDark)} labelFormatter={(p) => `PCI ${fmtPci(p)}`}
              formatter={(v) => [vfmt(v), MEASURES[measure].label]} />
            <Area dataKey={iso} stroke={color} fill={color} fillOpacity={0.5} strokeWidth={2} isAnimationActive={false} />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="panel p-4">
          <div className="label mb-2">Total exports over time</div>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={trend} margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
              <CartesianGrid stroke={ac.grid} strokeDasharray="3 3" />
              <XAxis dataKey="year" tick={{ fill: ac.tick, fontSize: 11 }} />
              <YAxis tick={{ fill: ac.tick, fontSize: 11 }} tickFormatter={(v) => `$${Math.round(v)}B`} width={52} />
              <Tooltip contentStyle={tooltipStyle(isDark)} formatter={(v) => [fmtB(v, 1), 'Total']} />
              <Line dataKey="total" stroke={color} dot={false} strokeWidth={2} isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="panel p-4">
          <div className="label mb-2">Average export complexity over time</div>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={trend} margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
              <CartesianGrid stroke={ac.grid} strokeDasharray="3 3" />
              <XAxis dataKey="year" tick={{ fill: ac.tick, fontSize: 11 }} />
              <YAxis tick={{ fill: ac.tick, fontSize: 11 }} tickFormatter={fmtPci} width={44} domain={['auto', 'auto']} />
              <Tooltip contentStyle={tooltipStyle(isDark)} formatter={(v) => [fmtPci(v), 'Mean PCI']} />
              <ReferenceLine y={0} stroke={ac.grid} />
              <Line dataKey="mpci" stroke="#22d3ee" dot={false} strokeWidth={2} isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
