import { useMemo } from 'react'
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, Legend,
} from 'recharts'
import { fmtPct, fmtPci, colorFor } from '../lib/format.js'
import { axisColors, tooltipStyle } from '../lib/chartTheme.js'
import { YearStepper } from './Controls.jsx'
import { useDarkMode } from '../lib/useDarkMode.jsx'

export default function AboutPanel({ data, year, setYear }) {
  const { isDark } = useDarkMode()
  const { coverage, meta } = data
  const ac = axisColors(isDark)
  const yi = coverage.years.indexOf(year)

  const rows = useMemo(() => coverage.grid.map((pci, gi) => {
    const row = { pci }
    coverage.thresholds.forEach((t, ti) => { row[`top${t}`] = coverage.coverage[ti][yi]?.[gi] })
    return row
  }), [coverage, yi])

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 items-start">
      <div className="panel p-4 space-y-3">
        <div className="label">Top-N world-export coverage by complexity · {year}</div>
        <YearStepper years={meta.years} year={year} onChange={setYear} />
        <ResponsiveContainer width="100%" height={260}>
          <LineChart data={rows} margin={{ top: 4, right: 16, bottom: 4, left: 8 }}>
            <CartesianGrid stroke={ac.grid} strokeDasharray="3 3" />
            <XAxis dataKey="pci" type="number" domain={['dataMin', 'dataMax']} tickFormatter={fmtPci}
              tick={{ fill: ac.tick, fontSize: 11 }} />
            <YAxis tick={{ fill: ac.tick, fontSize: 11 }} tickFormatter={(v) => `${Math.round(v * 100)}%`} domain={[0, 1]} width={48} />
            <ReferenceLine y={0.9} stroke={ac.tick} strokeDasharray="4 4" label={{ value: '90%', fill: ac.tick, fontSize: 10 }} />
            <Tooltip contentStyle={tooltipStyle(isDark)} labelFormatter={(p) => `PCI ${fmtPci(p)}`} formatter={(v, n) => [fmtPct(v, 1), n]} />
            <Legend verticalAlign="top" height={22} wrapperStyle={{ fontSize: 11 }} />
            {coverage.thresholds.map((t, ti) => (
              <Line key={t} dataKey={`top${t}`} name={`Top ${t}`} stroke={['#3b82f6', '#eab308', '#22d3ee'][ti] || colorFor(ti)} dot={false} strokeWidth={2} isAnimationActive={false} />
            ))}
          </LineChart>
        </ResponsiveContainer>
        <div className="text-[11px] text-slate-400 text-center -mt-1">PCI (Product Complexity Index)</div>
        <p className="text-xs text-slate-500">
          Coverage is lowest at the low-complexity (commodity) end, where exporters are fragmented,
          and highest in mid/high complexity. The top-20 average ~72% of world trade; top-50 ~93%.
        </p>
      </div>

      <div className="panel p-5 prose-sm max-w-none text-sm leading-relaxed text-slate-600 dark:text-slate-300 space-y-3">
        <h2 className="text-base font-semibold text-slate-900 dark:text-white">About this dashboard</h2>
        <p>
          Non-parametric view of global exports across the <strong>Product Complexity Index (PCI)</strong>,
          {' '}2000–2024, from the Harvard Growth Lab <em>Atlas of Economic Complexity</em> (HS92, HS4 level).
          Two estimands: a country's <strong>market share</strong> of world exports at each complexity
          (value-weighted local-linear regression) and the <strong>distribution of export value</strong>
          {' '}across complexity (value-weighted kernel density).
        </p>
        <p>
          <strong>Reading PCI:</strong> the index is standardized within each year, so compare
          value-weighted <em>shifts</em> across years, not absolute levels. Low PCI ≈ raw materials and
          commodities; high PCI ≈ machinery, electronics, chemicals, and instruments.
        </p>
        <p>
          Shares across <em>all</em> countries sum to 100% by construction (the local-linear estimator
          reproduces constants); the dollar distribution conserves total exports exactly, with only
          mean-zero redistribution across complexity. Source data is reconciled upstream
          (Bustos–Yildirim mirror reconciliation).
        </p>
        <p>
          <strong>Tech &amp; AI baskets.</strong> "AI compute" follows the Federal Reserve definition
          (HS 8471.50 / 8471.80 / 8473.30 — AI servers and accelerator/GPU cards). The semiconductor
          value-chain categories follow the OECD's mapping. These use the Atlas <strong>HS 2012</strong>
          vintage (2012–2024), since the relevant HS6 codes do not exist in HS92.
        </p>

        <h3 className="text-sm font-semibold text-slate-900 dark:text-white pt-1">Data &amp; references</h3>
        <ul className="space-y-1.5 text-sm">
          {[
            ['Atlas of Economic Complexity — Harvard Growth Lab (trade data, PCI)', 'https://atlas.hks.harvard.edu/'],
            ['HS92 trade data · Harvard Dataverse (doi:10.7910/DVN/T4CHWJ)', 'https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/T4CHWJ'],
            ['HS2012 trade data · Harvard Dataverse (doi:10.7910/DVN/YAVJDF)', 'https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/YAVJDF'],
            ['Fed — “The Global Trade Effects of the AI Infrastructure Boom” (FEDS Note, 2026-02-13)', 'https://www.federalreserve.gov/econres/notes/feds-notes/the-global-trade-effects-of-the-ai-infrastructure-boom-20260213.html'],
            ['OECD — “Mapping the semiconductor value chain” / HS code list (doi:10.1787/4154cdbf-en)', 'https://www.oecd.org/en/publications/promoting-the-development-of-the-semiconductor-ecosystem-in-mexico_02c81dec-en/full-report/list-of-harmonized-system-hs-codes-for-semiconductor-related-products_1369575a.html'],
          ].map(([label, href]) => (
            <li key={href} className="flex gap-2">
              <span className="text-slate-400">›</span>
              <a href={href} target="_blank" rel="noopener noreferrer"
                className="text-indigo-600 dark:text-indigo-400 hover:underline">{label}</a>
            </li>
          ))}
        </ul>
        <p className="text-xs text-slate-500 pt-1">{meta.source}</p>
        <p className="text-xs text-slate-500">
          Methods &amp; code: <a href="https://github.com/jasonzhixinglu/global-export-complexity"
            target="_blank" rel="noopener noreferrer"
            className="text-indigo-600 dark:text-indigo-400 hover:underline">github.com/jasonzhixinglu/global-export-complexity</a>
        </p>
      </div>
    </div>
  )
}
