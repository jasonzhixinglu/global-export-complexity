import { useMemo } from 'react'
import {
  ResponsiveContainer, BarChart, Bar, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Cell,
} from 'recharts'
import { distinctColor, fmtPct, fmtB } from '../lib/format.js'
import { axisColors, tooltipStyle } from '../lib/chartTheme.js'
import { Toggle, YearStepper } from './Controls.jsx'
import { useDarkMode } from '../lib/useDarkMode.jsx'
import { useSessionState } from '../lib/sessionState.js'

// Bilateral trade network for a tech product group: where an anchor's flow goes, by partner
// country, as value or share, over time + ranked for the selected year.
export default function TechCorridorView({ data, year, setYear }) {
  const { isDark } = useDarkMode()
  const { byIso, colorByIso } = data
  const tb = data.techaiBilateral
  // options persist across tab switches (sessionStorage)
  const [basketId, setBasketId] = useSessionState('techc-basket', 'ai')
  const [anchor, setAnchor] = useSessionState('techc-anchor', 'TWN')
  const [role, setRole] = useSessionState('techc-role', 'origin')      // exports from / imports to
  const [metric, setMetric] = useSessionState('techc-metric', 'share')  // share of anchor's flow / value $B
  const ac = axisColors(isDark)

  if (!tb) return <div className="panel p-6 text-sm text-slate-400">Tech corridor data not available.</div>

  const basket = tb.baskets.find(b => b.id === basketId) || tb.baskets[0]
  const ty = Math.min(tb.years[tb.years.length - 1], Math.max(tb.years[0], year))
  const nameOf = (iso) => iso === 'ROW' ? 'Rest of world' : (byIso[iso]?.name || iso)
  const flowWord = role === 'origin' ? 'exports' : 'imports'
  const otherWord = role === 'origin' ? 'destinations' : 'origins'
  const V = tb.value[basket.id] || {}

  const cell = (partner, yr) => role === 'origin'
    ? V[anchor]?.[partner]?.[String(yr)] : V[partner]?.[anchor]?.[String(yr)]
  const partnersAll = role === 'origin'
    ? Object.keys(V[anchor] || {})
    : Object.keys(V).filter(o => V[o]?.[anchor])
  const labelOf = (g) => nameOf(g)

  // per-partner value (and anchor total) for a year — partners are countries (+ ROW), not regions:
  // for tech the interesting counterparties are specific economies (China vs Taiwan vs US).
  const groupVals = (yr) => {
    const gv = {}; let tot = 0
    for (const p of partnersAll) {
      const v = cell(p, yr); if (!v) continue
      tot += v; gv[p] = (gv[p] || 0) + v
    }
    return { gv, tot }
  }

  const rankedYear = useMemo(() => {
    const { gv } = groupVals(ty)
    return Object.entries(gv).map(([g, v]) => ({ g, v })).sort((a, b) => b.v - a.v)
  }, [tb, basket.id, anchor, role, ty])

  const topGroups = rankedYear.slice(0, 7).map(r => r.g)
  // persistent per-country colour (ROW gets its own stable slot) so partners keep their colour
  // across years and rank swaps -- not colour-by-rank.
  const cOf = (g) => distinctColor(g === 'ROW' ? 50 : (colorByIso[g] ?? 63))

  const series = useMemo(() => tb.years.map(yr => {
    const { gv, tot } = groupVals(yr)
    const row = { year: yr }
    for (const g of topGroups) {
      const v = gv[g] || 0
      row[g] = metric === 'share' ? (tot ? v / tot : 0) : v
    }
    return row
  }), [tb, basket.id, anchor, role, metric, topGroups])

  const totY = rankedYear.reduce((s, r) => s + r.v, 0)
  const isPct = metric === 'share'
  const vfmt = isPct ? (v) => fmtPct(v, 1) : (v) => fmtB(v, 1)
  const axfmt = isPct ? (v) => `${Math.round(v * 100)}%` : (v) => `$${Math.round(v)}B`
  const barData = rankedYear.slice(0, 12).map(r => ({ g: r.g, v: isPct ? (totY ? r.v / totY : 0) : r.v }))

  return (
    <div className="space-y-3">
      <div className="panel p-4 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="label">Year</span>
            <YearStepper years={tb.years} year={ty} onChange={setYear} />
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Toggle value={role} onChange={setRole}
              options={[{ value: 'origin', label: 'Exports from' }, { value: 'dest', label: 'Imports to' }]} />
            <select value={anchor} onChange={e => setAnchor(e.target.value)}
              className="bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 cursor-pointer border border-slate-300 dark:border-slate-600 rounded px-2 py-1 text-sm">
              {tb.blocs.map(b => <option key={b} value={b}>{nameOf(b)}</option>)}
            </select>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-x-2 gap-y-1.5 border-t border-slate-200 dark:border-slate-800 pt-3">
          <span className="label mr-0.5">Product</span>
          {tb.baskets.map(b => (
            <button key={b.id} onClick={() => setBasketId(b.id)}
              className={`chip ${basket.id === b.id ? 'chip-on' : 'chip-off'}`}>{b.label}</button>
          ))}
          <span className="mx-1 w-px self-stretch bg-slate-200 dark:bg-slate-700" />
          <Toggle value={metric} onChange={setMetric}
            options={[{ value: 'share', label: 'Share' }, { value: 'value', label: 'Value ($B)' }]} />
        </div>
        <div className="text-xs text-slate-500">
          {role === 'origin' ? `${nameOf(anchor)}’s ${basket.label} exports by ${otherWord}`
            : `${basket.label} ${flowWord} into ${nameOf(anchor)} by ${otherWord}`}
          {' '}· {fmtB(totY, 1)} from {nameOf(anchor)} ({ty})
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <div className="panel p-3 min-w-0">
          <div className="label mb-2">Top {otherWord} — {nameOf(anchor)}, {ty}</div>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={barData} layout="vertical" margin={{ left: 6, right: 16 }}>
              <CartesianGrid stroke={ac.grid} strokeDasharray="2 2" horizontal={false} />
              <XAxis type="number" tick={{ fill: ac.tick, fontSize: 10 }} tickFormatter={axfmt} />
              <YAxis type="category" dataKey="g" width={44} tick={{ fill: ac.tick, fontSize: 10 }} />
              <Tooltip contentStyle={tooltipStyle(isDark)} formatter={(v) => [vfmt(v), basket.label]}
                labelFormatter={labelOf} />
              <Bar dataKey="v" isAnimationActive={false}>
                {barData.map(d => <Cell key={d.g} fill={cOf(d.g)} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="panel p-3 min-w-0">
          <div className="label mb-2">{metric === 'share' ? 'Share' : 'Value'} over time — top {otherWord}</div>
          <ResponsiveContainer width="100%" height={400}>
            <AreaChart data={series} margin={{ top: 8, right: 16, bottom: 8, left: 6 }}>
              <CartesianGrid stroke={ac.grid} strokeDasharray="2 2" />
              <XAxis dataKey="year" tick={{ fill: ac.tick, fontSize: 10 }} />
              <YAxis tick={{ fill: ac.tick, fontSize: 10 }} tickFormatter={axfmt} width={48}
                domain={isPct ? [0, 1] : [0, 'auto']} />
              <Tooltip contentStyle={tooltipStyle(isDark)} formatter={(v, n) => [vfmt(v), labelOf(n)]} />
              {topGroups.map(g => (
                <Area key={g} type="monotone" dataKey={g} stackId="1" stroke={cOf(g)} fill={cOf(g)}
                  fillOpacity={0.7} strokeWidth={1} isAnimationActive={false} />
              ))}
            </AreaChart>
          </ResponsiveContainer>
          <div className="flex flex-wrap gap-x-3 gap-y-1 mt-2">
            {topGroups.map(g => (
              <span key={g} className="inline-flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-300">
                <span className="w-2 h-2 rounded-full" style={{ background: cOf(g) }} />{labelOf(g)}
              </span>
            ))}
          </div>
        </div>
      </div>

      <p className="text-xs text-slate-400 px-1">
        Bilateral flows for the OECD value-chain + Fed AI-compute HS6 baskets (HS2012, 2012–2024) —
        the same baskets as the “By country” view. One flow read two ways: {nameOf(anchor)}’s
        {' '}{basket.label} exports to a partner are that partner’s imports from {nameOf(anchor)}.
        “Share” = the partner’s % of {nameOf(anchor)}’s {basket.label} {flowWord}; stacked top
        {' '}{otherWord} (the gap to 100% is smaller partners).
      </p>
    </div>
  )
}
