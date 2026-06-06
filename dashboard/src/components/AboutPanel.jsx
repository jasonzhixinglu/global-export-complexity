import { useMemo, useState } from 'react'
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, Legend,
} from 'recharts'
import { fmtPct, fmtPci, colorFor } from '../lib/format.js'
import { axisColors, tooltipStyle } from '../lib/chartTheme.js'
import { YearStepper, Toggle } from './Controls.jsx'
import { useDarkMode } from '../lib/useDarkMode.jsx'

const REFS = [
  ['Atlas of Economic Complexity — Harvard Growth Lab (trade data & PCI)', 'https://atlas.hks.harvard.edu/'],
  ['HS92 trade data · Harvard Dataverse (doi:10.7910/DVN/T4CHWJ)', 'https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/T4CHWJ'],
  ['HS2012 trade data · Harvard Dataverse (doi:10.7910/DVN/YAVJDF)', 'https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/YAVJDF'],
  ['Fed — “The Global Trade Effects of the AI Infrastructure Boom” (FEDS Note, 2026-02-13)', 'https://www.federalreserve.gov/econres/notes/feds-notes/the-global-trade-effects-of-the-ai-infrastructure-boom-20260213.html'],
  ['OECD (2025) — “Mapping the semiconductor value chain” / HS code list (doi:10.1787/4154cdbf-en)', 'https://www.oecd.org/en/publications/promoting-the-development-of-the-semiconductor-ecosystem-in-mexico_02c81dec-en/full-report/list-of-harmonized-system-hs-codes-for-semiconductor-related-products_1369575a.html'],
  ['Hidalgo & Hausmann (2009) — “The building blocks of economic complexity”, PNAS', 'https://www.pnas.org/doi/10.1073/pnas.0900943106'],
  ['Methods & code (this project)', 'https://github.com/jasonzhixinglu/global-export-complexity'],
]

function Acc({ title, open, onToggle, children }) {
  return (
    <div className="border-b border-slate-200 dark:border-slate-800 last:border-0">
      <button onClick={onToggle}
        className="w-full flex items-center justify-between py-2.5 text-left group">
        <span className="text-sm font-medium text-slate-800 dark:text-slate-100 group-hover:text-indigo-500">{title}</span>
        <span className="text-slate-400 text-lg leading-none w-5 text-center">{open ? '–' : '+'}</span>
      </button>
      {open && (
        <div className="pb-3 text-sm leading-relaxed text-slate-600 dark:text-slate-300 space-y-2">{children}</div>
      )}
    </div>
  )
}

export default function AboutPanel({ data, year, setYear, flow, setFlow }) {
  const { isDark } = useDarkMode()
  const { coverage, meta } = data
  const ac = axisColors(isDark)
  const yi = coverage.years.indexOf(year)
  const fl = flow === 'import' ? 'import' : 'export'
  const flowWord = fl === 'import' ? 'importers' : 'exporters'
  const cov = (coverage.coverage[fl] || coverage.coverage.export || coverage.coverage)
  const [open, setOpen] = useState(null)  // Overview is always shown; the rest are single-open
  const sec = (title) => ({ open: open === title, onToggle: () => setOpen(s => (s === title ? null : title)) })

  const rows = useMemo(() => coverage.grid.map((pci, gi) => {
    const row = { pci }
    coverage.thresholds.forEach((t, ti) => { row[`top${t}`] = cov[ti][yi]?.[gi] })
    return row
  }), [coverage, yi, cov])

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 items-start">
      <div className="panel p-4 space-y-3">
        <div className="flex items-center justify-between gap-2">
          <div className="label">Top-N world-{fl} coverage by complexity · {year}</div>
          <Toggle value={fl} onChange={setFlow}
            options={[{ value: 'export', label: 'Exports' }, { value: 'import', label: 'Imports' }]} />
        </div>
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
          Cumulative share of world {fl} held by the top-N {flowWord}, by complexity. Coverage is
          lowest at the low-complexity (commodity) end, where {flowWord} are fragmented, and highest
          in mid/high complexity.
        </p>
      </div>

      <div className="panel px-4 py-1">
        <div className="border-b border-slate-200 dark:border-slate-800 py-2.5">
          <div className="text-sm font-medium text-slate-800 dark:text-slate-100 mb-1.5">Overview</div>
          <p className="text-sm leading-relaxed text-slate-600 dark:text-slate-300">
            A non-parametric view of global exports across the <strong>Product Complexity Index
            (PCI)</strong>, 2000–2024, from the Harvard Growth Lab <em>Atlas of Economic
            Complexity</em>. The <strong>Explorer</strong> shows, for any set of countries, either
            their <strong>market share</strong> of world exports at each complexity level or the
            <strong> distribution of their export value</strong> across complexity; click the chart
            (or drag the slider) to see the largest products near a chosen PCI. The
            <strong> Tech &amp; AI</strong> tab tracks exports of AI-compute hardware and the
            semiconductor value chain — by country, year, world share, and share of each country's
            own exports.
          </p>
        </div>

        <Acc title="Estimation method" {...sec('Estimation method')}>
          <p>
            <strong>Market share by complexity</strong> is a value-weighted <em>local-linear</em>
            kernel regression of each country's product-level share on PCI (Gaussian kernel,
            bandwidth 0.10). Local-linear is used over Nadaraya–Watson for its lower boundary bias;
            it also reproduces constants, so shares across all countries sum to 100% by construction.
          </p>
          <p>
            <strong>Export-value distribution</strong> is a value-weighted Gaussian <em>kernel
            density</em> over PCI (same bandwidth). A lower bandwidth is used deliberately to retain
            multi-hump structure rather than over-smooth.
          </p>
          <p className="text-xs text-slate-500">
            Refs: Fan &amp; Gijbels (1996), <em>Local Polynomial Modelling</em>; Silverman (1986),
            <em> Density Estimation</em>; Hidalgo &amp; Hausmann (2009), PNAS (ECI/PCI).
          </p>
        </Acc>

        <Acc title="Reading the PCI axis" {...sec('Reading the PCI axis')}>
          <p>
            PCI is standardised within each year's cross-section, so compare value-weighted
            <em> shifts</em> across years, not absolute levels. Low PCI ≈ raw materials and
            commodities; high PCI ≈ machinery, electronics, chemicals and instruments.
          </p>
        </Acc>

        <Acc title="Tech & AI baskets" {...sec('Tech & AI baskets')}>
          <p>
            <strong>AI compute</strong> follows the Fed FEDS Note (HS 8471.50 / 8471.80 / 8473.30 —
            AI servers and accelerator/GPU cards). The <strong>semiconductor</strong> categories
            follow the OECD value-chain mapping (chips, photosensitive devices, raw materials,
            manufacturing equipment, foundry and wafer inputs). These use the Atlas
            <strong> HS 2012</strong> vintage (2012–2024), since the relevant HS6 codes do not exist
            in HS92. The two sets are disjoint, so <em>All</em> = their sum with no double-counting.
          </p>
        </Acc>

        <Acc title="Caveats" {...sec('Caveats')}>
          <p>
            Source trade data is reconciled upstream (Bustos–Yildirim / BACI-style mirror
            reconciliation). Coverage of a top-N set is genuinely lowest at low complexity, where
            many small commodity exporters compete. Displayed shares are clipped to [0, 1]; the
            adding-up identity holds on the unclipped estimates.
          </p>
        </Acc>

        <Acc title="Data & references" {...sec('Data & references')}>
          <ul className="space-y-1.5">
            {REFS.map(([label, href]) => (
              <li key={href} className="flex gap-2">
                <span className="text-slate-400">›</span>
                <a href={href} target="_blank" rel="noopener noreferrer"
                  className="text-indigo-600 dark:text-indigo-400 hover:underline">{label}</a>
              </li>
            ))}
          </ul>
          <p className="text-xs text-slate-500 pt-1">{meta.source}</p>
        </Acc>
      </div>
    </div>
  )
}
