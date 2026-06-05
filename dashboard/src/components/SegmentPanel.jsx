import { useMemo, useState } from 'react'
import {
  ResponsiveContainer, BarChart, Bar, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Cell,
} from 'recharts'
import { MEASURES } from '../lib/data.js'
import { colorFor, fmtPct, fmtB, fmtPci } from '../lib/format.js'
import { axisColors, tooltipStyle } from '../lib/chartTheme.js'
import { MeasureToggle, YearSlider, Toggle } from './Controls.jsx'
import { useDarkMode } from '../lib/useDarkMode.jsx'

const BANDS = [
  { id: 'low', label: 'Low (≤ −1)', lo: -2.5, hi: -1 },
  { id: 'mid', label: 'Mid (−1…+1)', lo: -1, hi: 1 },
  { id: 'high', label: 'High (≥ +1)', lo: 1, hi: 2.5 },
  { id: 'all', label: 'All', lo: -2.5, hi: 2.5 },
]

// metric for one country/year within [lo,hi]
function bandMetric(data, iso, year, measure, band) {
  const { meta, series } = data
  const y = String(year)
  if (measure === 'share') {
    const g = meta.shareGrid
    let sum = 0, n = 0
    for (let i = 0; i < g.length; i++) {
      if (g[i] >= band.lo && g[i] <= band.hi) { const v = series.share[iso]?.[y]?.[i]; if (v != null) { sum += v; n++ } }
    }
    return n ? sum / n : null            // average market share across the band
  }
  // value / density: integrate density (× total for value) over the band
  const g = meta.kdeGrid
  const dx = g.length > 1 ? g[1] - g[0] : 1
  const dens = series.density[iso]?.[y]
  if (!dens) return null
  let frac = 0
  for (let i = 0; i < g.length; i++) if (g[i] >= band.lo && g[i] <= band.hi) frac += (dens[i] || 0) * dx
  if (measure === 'density') return frac          // fraction of the country's exports in the band
  const t = series.totalB[iso]?.[y]
  return t != null ? frac * t : null              // $B in the band
}

export default function SegmentPanel({ data, year, setYear, measure, setMeasure }) {
  const { isDark } = useDarkMode()
  const { meta, byIso, colorByIso } = data
  const [bandId, setBandId] = useState('high')
  const band = BANDS.find(b => b.id === bandId)
  const ac = axisColors(isDark)
  const isos = meta.countries.map(c => c.iso3)

  const ranked = useMemo(() => isos
    .map(iso => ({ iso, name: byIso[iso].name, v: bandMetric(data, iso, year, measure, band) }))
    .filter(d => d.v != null)
    .sort((a, b) => b.v - a.v), [data, year, measure, band, isos, byIso])

  const topIsos = ranked.slice(0, 6).map(d => d.iso)
  const timeSeries = useMemo(() => meta.years.map(yr => {
    const row = { year: yr }
    for (const iso of topIsos) row[iso] = bandMetric(data, iso, yr, measure, band)
    return row
  }), [data, measure, band, topIsos, meta.years])

  const vfmt = measure === 'share' ? (v) => fmtPct(v, 2) : measure === 'value' ? (v) => fmtB(v, 1) : (v) => fmtPct(v, 1)
  const axfmt = measure === 'share' ? (v) => `${Math.round(v * 100)}%` : measure === 'value' ? (v) => `$${Math.round(v)}B` : (v) => `${Math.round(v * 100)}%`
  const metricLabel = measure === 'share' ? 'Avg market share in band'
    : measure === 'value' ? 'Export value in band' : 'Share of own exports in band'

  return (
    <div className="space-y-4">
      <div className="panel p-4 space-y-3">
        <div className="flex flex-wrap items-center gap-3 justify-between">
          <div className="flex items-center gap-2">
            <span className="label">Complexity band</span>
            <Toggle value={bandId} onChange={setBandId} options={BANDS.map(b => ({ value: b.id, label: b.label }))} />
          </div>
          <MeasureToggle value={measure} onChange={setMeasure} measures={MEASURES} />
        </div>
        <YearSlider years={meta.years} year={year} onChange={setYear} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="panel p-4">
          <div className="label mb-2">{metricLabel} — {band.label}, {year}</div>
          <ResponsiveContainer width="100%" height={420}>
            <BarChart data={ranked.slice(0, 15)} layout="vertical" margin={{ left: 8, right: 16 }}>
              <CartesianGrid stroke={ac.grid} strokeDasharray="3 3" horizontal={false} />
              <XAxis type="number" tick={{ fill: ac.tick, fontSize: 11 }} tickFormatter={axfmt} />
              <YAxis type="category" dataKey="iso" width={44} tick={{ fill: ac.tick, fontSize: 11 }} />
              <Tooltip contentStyle={tooltipStyle(isDark)} formatter={(v, _n, p) => [vfmt(v), byIso[p.payload.iso]?.name]} />
              <Bar dataKey="v" isAnimationActive={false}>
                {ranked.slice(0, 15).map(d => <Cell key={d.iso} fill={colorFor(colorByIso[d.iso])} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="panel p-4">
          <div className="label mb-2">Top 6 over time — {band.label}</div>
          <ResponsiveContainer width="100%" height={420}>
            <LineChart data={timeSeries} margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
              <CartesianGrid stroke={ac.grid} strokeDasharray="3 3" />
              <XAxis dataKey="year" tick={{ fill: ac.tick, fontSize: 11 }} />
              <YAxis tick={{ fill: ac.tick, fontSize: 11 }} tickFormatter={axfmt} width={52} />
              <Tooltip contentStyle={tooltipStyle(isDark)} formatter={(v, n) => [vfmt(v), byIso[n]?.name || n]} />
              {topIsos.map(iso => (
                <Line key={iso} dataKey={iso} stroke={colorFor(colorByIso[iso])} dot={false} strokeWidth={2} isAnimationActive={false} />
              ))}
            </LineChart>
          </ResponsiveContainer>
          <div className="flex flex-wrap gap-2 mt-2">
            {topIsos.map(iso => (
              <span key={iso} className="text-xs flex items-center gap-1">
                <span className="w-2 h-2 rounded-full" style={{ background: colorFor(colorByIso[iso]) }} />{iso}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
