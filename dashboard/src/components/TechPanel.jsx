import { useMemo, useState } from 'react'
import {
  ResponsiveContainer, BarChart, Bar, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Cell,
} from 'recharts'
import { colorFor, fmtPct, fmtB } from '../lib/format.js'
import { axisColors, tooltipStyle } from '../lib/chartTheme.js'
import { Toggle, YearStepper } from './Controls.jsx'
import { useDarkMode } from '../lib/useDarkMode.jsx'

export default function TechPanel({ data, year, setYear, flow, setFlow }) {
  const { isDark } = useDarkMode()
  const t = data.techai
  const { byIso } = data
  const [basketId, setBasketId] = useState('all')
  const [tm, setTm] = useState('share')
  const ac = axisColors(isDark)
  const fl = flow === 'import' ? 'import' : 'export'
  const flowWord = fl === 'import' ? 'imports' : 'exports'

  if (!t) return <div className="panel p-6 text-sm text-slate-400">Tech & AI data not available.</div>

  const METRICS = [
    { value: 'share', label: 'World share' },
    { value: 'value', label: fl === 'import' ? 'Import value' : 'Export value' },
    { value: 'own', label: `% of own ${flowWord}` },
  ]
  const valueB = t.valueB[fl] || t.valueB.export || t.valueB
  const worldBF = t.worldB[fl] || t.worldB.export || t.worldB
  const ownTotalF = (t.countryTotalB[fl] || t.countryTotalB.export || t.countryTotalB)

  const basket = t.baskets.find(b => b.id === basketId) || t.baskets[0]
  const ty = Math.min(t.years[t.years.length - 1], Math.max(t.years[0], year))  // clamp to HS12 range
  const y = String(ty)
  const world = worldBF[basket.id]?.[y]

  const metric = (iso, yr) => {
    const v = valueB[basket.id]?.[iso]?.[String(yr)]
    if (v == null) return null
    if (tm === 'value') return v
    if (tm === 'own') {
      const own = ownTotalF?.[iso]?.[String(yr)]
      return own ? v / own : null
    }
    const w = worldBF[basket.id]?.[String(yr)]
    return w ? v / w : null
  }

  const ranked = useMemo(() => t.countries
    .map(iso => ({ iso, v: metric(iso, ty) }))
    .filter(d => d.v != null && d.v > 0)
    .sort((a, b) => b.v - a.v), [t, basket.id, ty, tm, fl])

  // colour by rank in the current list (distinct across the shown bars/lines; no global-index wrap)
  const colorByRank = useMemo(() => {
    const m = {}; ranked.forEach((d, i) => { m[d.iso] = colorFor(i) }); return m
  }, [ranked])
  const cOf = (iso) => colorByRank[iso] || '#94a3b8'

  const topIsos = ranked.slice(0, 6).map(d => d.iso)
  const series = useMemo(() => t.years.map(yr => {
    const row = { year: yr }
    for (const iso of topIsos) row[iso] = metric(iso, yr)
    return row
  }), [t, basket.id, tm, topIsos, fl])

  const isPct = tm !== 'value'
  const vfmt = isPct ? (v) => fmtPct(v, 1) : (v) => fmtB(v, 1)
  const axfmt = isPct ? (v) => `${Math.round(v * 100)}%` : (v) => `$${Math.round(v)}B`
  const metricLabel = tm === 'value' ? (fl === 'import' ? 'Import value' : 'Export value')
    : tm === 'own' ? `Share of own ${flowWord}` : 'World market share'
  const topShare = tm === 'share' ? ranked.slice(0, 3).reduce((s, d) => s + d.v, 0) : 0
  const stacked = tm !== 'own'  // share and value are additive across countries; "% of own" is not

  return (
    <div className="space-y-3">
      <div className="panel p-4 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="label">Year</span>
            <YearStepper years={t.years} year={ty} onChange={setYear} />
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Toggle value={fl} onChange={setFlow}
              options={[{ value: 'export', label: 'Exports' }, { value: 'import', label: 'Imports' }]} />
            <Toggle value={tm} onChange={setTm} options={METRICS} />
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-x-2 gap-y-1.5 border-t border-slate-200 dark:border-slate-800 pt-3">
          <span className="label mr-0.5">Category</span>
          <button onClick={() => setBasketId('all')}
            className={`chip ${basketId === 'all' ? 'chip-on' : 'chip-off'}`}>All</button>
          {t.baskets.filter(b => b.parent === 'all').map(b => (
            <button key={b.id} onClick={() => setBasketId(b.id)}
              className={`chip ${basketId === b.id ? 'chip-on' : 'chip-off'}`}>{b.label}</button>
          ))}
        </div>
        <div className="text-xs text-slate-500">
          {basket.nCodes} HS6 codes · world {fmtB(world, 1)} ({ty}){' '}
          {tm === 'share' && topShare ? `· top-3 = ${fmtPct(topShare, 0)} of world` : ''}
          {tm === 'own' ? `· basket as a share of each country’s total ${flowWord}` : ''}
          {' · '}HS2012 data
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <div className="panel p-3 min-w-0">
          <div className="label mb-2">{metricLabel} — {basket.label}, {ty}</div>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={ranked.slice(0, 14)} layout="vertical" margin={{ left: 6, right: 16 }}>
              <CartesianGrid stroke={ac.grid} strokeDasharray="2 2" horizontal={false} />
              <XAxis type="number" tick={{ fill: ac.tick, fontSize: 10 }} tickFormatter={axfmt} />
              <YAxis type="category" dataKey="iso" width={42} tick={{ fill: ac.tick, fontSize: 10 }} />
              <Tooltip contentStyle={tooltipStyle(isDark)} formatter={(v, _n, p) => [vfmt(v), byIso[p.payload.iso]?.name]} />
              <Bar dataKey="v" isAnimationActive={false}>
                {ranked.slice(0, 14).map(d => <Cell key={d.iso} fill={cOf(d.iso)} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="panel p-3 min-w-0">
          <div className="label mb-2">Top 6 over time {stacked ? '(stacked share)' : ''} — {metricLabel}</div>
          <ResponsiveContainer width="100%" height={400}>
            <AreaChart data={series} margin={{ top: 8, right: 16, bottom: 8, left: 6 }}>
              <CartesianGrid stroke={ac.grid} strokeDasharray="2 2" />
              <XAxis dataKey="year" tick={{ fill: ac.tick, fontSize: 10 }} />
              <YAxis tick={{ fill: ac.tick, fontSize: 10 }} tickFormatter={axfmt} width={48} />
              <Tooltip contentStyle={tooltipStyle(isDark)} formatter={(v, n) => [vfmt(v), byIso[n]?.name || n]} />
              {topIsos.map(iso => (
                <Area key={iso} dataKey={iso} stackId={stacked ? '1' : undefined}
                  stroke={cOf(iso)} fill={cOf(iso)}
                  fillOpacity={stacked ? 0.7 : 0.12} strokeWidth={1.5} isAnimationActive={false} />
              ))}
            </AreaChart>
          </ResponsiveContainer>
          <div className="flex flex-wrap gap-x-3 gap-y-1 mt-2">
            {topIsos.map(iso => (
              <span key={iso} className="inline-flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-300">
                <span className="w-2 h-2 rounded-full" style={{ background: cOf(iso) }} />
                {byIso[iso]?.name || iso}
              </span>
            ))}
          </div>
        </div>
      </div>
      <p className="text-xs text-slate-400 px-1">
        AI compute = Fed FEDS Note basket (HS 847150/847180/847330). Semiconductor stages = OECD (2025)
        value chain. HS2012 data. “World share” = of world {flowWord} in the basket; “% of own {flowWord}” =
        basket value ÷ the country’s total {flowWord}.
      </p>
    </div>
  )
}
