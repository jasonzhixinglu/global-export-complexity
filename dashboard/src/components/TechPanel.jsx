import { useMemo, useState } from 'react'
import {
  ResponsiveContainer, BarChart, Bar, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Cell,
} from 'recharts'
import { colorFor, fmtPct, fmtB } from '../lib/format.js'
import { axisColors, tooltipStyle } from '../lib/chartTheme.js'
import { Toggle, YearStepper } from './Controls.jsx'
import { useDarkMode } from '../lib/useDarkMode.jsx'

const METRICS = [
  { value: 'share', label: 'World share' },
  { value: 'value', label: 'Export value' },
  { value: 'own', label: '% of own exports' },
]

export default function TechPanel({ data, year, setYear }) {
  const { isDark } = useDarkMode()
  const t = data.techai
  const { byIso, colorByIso } = data
  const [basketId, setBasketId] = useState('ai')
  const [tm, setTm] = useState('share')
  const ac = axisColors(isDark)

  if (!t) return <div className="panel p-6 text-sm text-slate-400">Tech & AI data not available.</div>

  const basket = t.baskets.find(b => b.id === basketId) || t.baskets[0]
  const ty = Math.min(t.years[t.years.length - 1], Math.max(t.years[0], year))  // clamp to HS12 range
  const y = String(ty)
  const world = t.worldB[basket.id]?.[y]

  const metric = (iso, yr) => {
    const v = t.valueB[basket.id]?.[iso]?.[String(yr)]
    if (v == null) return null
    if (tm === 'value') return v
    if (tm === 'own') {
      const own = t.countryTotalB?.[iso]?.[String(yr)]
      return own ? v / own : null
    }
    const w = t.worldB[basket.id]?.[String(yr)]
    return w ? v / w : null
  }

  const ranked = useMemo(() => t.countries
    .map(iso => ({ iso, v: metric(iso, ty) }))
    .filter(d => d.v != null && d.v > 0)
    .sort((a, b) => b.v - a.v), [t, basket.id, ty, tm])

  const topIsos = ranked.slice(0, 6).map(d => d.iso)
  const series = useMemo(() => t.years.map(yr => {
    const row = { year: yr }
    for (const iso of topIsos) row[iso] = metric(iso, yr)
    return row
  }), [t, basket.id, tm, topIsos])

  const isPct = tm !== 'value'
  const vfmt = isPct ? (v) => fmtPct(v, 1) : (v) => fmtB(v, 1)
  const axfmt = isPct ? (v) => `${Math.round(v * 100)}%` : (v) => `$${Math.round(v)}B`
  const metricLabel = tm === 'value' ? 'Export value' : tm === 'own' ? 'Share of own exports' : 'World market share'
  const topShare = tm === 'share' ? ranked.slice(0, 3).reduce((s, d) => s + d.v, 0) : 0
  const stacked = tm === 'share'

  return (
    <div className="space-y-3">
      <div className="panel p-4 space-y-3">
        <div className="flex flex-wrap items-center gap-3 justify-between">
          <div className="flex items-center gap-2">
            <span className="label">Basket</span>
            <select value={basketId} onChange={e => setBasketId(e.target.value)}
              className="bg-transparent border border-slate-300 dark:border-slate-600 rounded px-3 py-1.5 text-sm">
              <option value="ai">AI compute (Fed)</option>
              <optgroup label="Semiconductor value chain (OECD)">
                {t.baskets.filter(b => b.id === 'semi' || b.parent === 'semi').map(b => (
                  <option key={b.id} value={b.id}>{b.label}</option>
                ))}
              </optgroup>
            </select>
          </div>
          <Toggle value={tm} onChange={setTm} options={METRICS} />
        </div>
        <YearStepper years={t.years} year={ty} onChange={setYear} />
        <div className="text-xs text-slate-500">
          {basket.nCodes} HS6 codes · world {fmtB(world, 1)} ({ty}){' '}
          {tm === 'share' && topShare ? `· top-3 = ${fmtPct(topShare, 0)} of world` : ''}
          {tm === 'own' ? '· basket as a share of each country’s total exports' : ''}
          {' · '}HS2012 data
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <div className="panel p-3">
          <div className="label mb-2">{metricLabel} — {basket.label}, {ty}</div>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={ranked.slice(0, 14)} layout="vertical" margin={{ left: 6, right: 16 }}>
              <CartesianGrid stroke={ac.grid} strokeDasharray="2 2" horizontal={false} />
              <XAxis type="number" tick={{ fill: ac.tick, fontSize: 10 }} tickFormatter={axfmt} />
              <YAxis type="category" dataKey="iso" width={42} tick={{ fill: ac.tick, fontSize: 10 }} />
              <Tooltip contentStyle={tooltipStyle(isDark)} formatter={(v, _n, p) => [vfmt(v), byIso[p.payload.iso]?.name]} />
              <Bar dataKey="v" isAnimationActive={false}>
                {ranked.slice(0, 14).map(d => <Cell key={d.iso} fill={colorFor(colorByIso[d.iso])} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="panel p-3">
          <div className="label mb-2">Top 6 over time {stacked ? '(stacked share)' : ''} — {metricLabel}</div>
          <ResponsiveContainer width="100%" height={400}>
            <AreaChart data={series} margin={{ top: 8, right: 16, bottom: 8, left: 6 }}>
              <CartesianGrid stroke={ac.grid} strokeDasharray="2 2" />
              <XAxis dataKey="year" tick={{ fill: ac.tick, fontSize: 10 }} />
              <YAxis tick={{ fill: ac.tick, fontSize: 10 }} tickFormatter={axfmt} width={48} />
              <Tooltip contentStyle={tooltipStyle(isDark)} formatter={(v, n) => [vfmt(v), byIso[n]?.name || n]} />
              {topIsos.map(iso => (
                <Area key={iso} dataKey={iso} stackId={stacked ? '1' : undefined}
                  stroke={colorFor(colorByIso[iso])} fill={colorFor(colorByIso[iso])}
                  fillOpacity={stacked ? 0.7 : 0.12} strokeWidth={1.5} isAnimationActive={false} />
              ))}
            </AreaChart>
          </ResponsiveContainer>
          <div className="flex flex-wrap gap-x-3 gap-y-1 mt-2">
            {topIsos.map(iso => (
              <span key={iso} className="inline-flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-300">
                <span className="w-2 h-2 rounded-full" style={{ background: colorFor(colorByIso[iso]) }} />
                {byIso[iso]?.name || iso}
              </span>
            ))}
          </div>
        </div>
      </div>
      <p className="text-xs text-slate-400 px-1">
        AI compute = Fed FEDS Note basket (HS 847150/847180/847330). Semiconductor stages = OECD (2025)
        value chain. HS2012 data. “World share” = of world exports in the basket; “% of own exports” =
        basket value ÷ the country’s total exports.
      </p>
    </div>
  )
}
