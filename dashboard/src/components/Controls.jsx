import { useEffect, useRef } from 'react'
import { colorFor, fmtPci } from '../lib/format.js'

export function MeasureToggle({ value, onChange, measures }) {
  return (
    <div className="seg-group">
      {Object.entries(measures).map(([k, m]) => (
        <button key={k} onClick={() => onChange(k)}
          className={`seg-btn ${value === k ? 'seg-btn-on' : ''}`} title={m.unit}>
          {m.label}
        </button>
      ))}
    </div>
  )
}

export function Toggle({ value, onChange, options }) {
  return (
    <div className="seg-group">
      {options.map(o => (
        <button key={o.value} onClick={() => onChange(o.value)}
          className={`seg-btn ${value === o.value ? 'seg-btn-on' : ''}`}>
          {o.label}
        </button>
      ))}
    </div>
  )
}

export function YearSlider({ years, year, onChange, playable = true }) {
  const playing = useRef(false)
  const timer = useRef(null)
  const stop = () => { playing.current = false; if (timer.current) clearInterval(timer.current); timer.current = null }
  useEffect(() => stop, [])
  const togglePlay = () => {
    if (playing.current) { stop(); return }
    playing.current = true
    timer.current = setInterval(() => {
      onChange(prev => {
        const i = years.indexOf(prev)
        if (i >= years.length - 1) return years[0]
        return years[i + 1]
      })
    }, 600)
  }
  return (
    <div className="flex items-center gap-3 w-full">
      {playable && (
        <button onClick={togglePlay}
          className="seg-btn seg-btn-on shrink-0 w-9 text-center" title="Play / pause across years">
          ▶
        </button>
      )}
      <input type="range" min={years[0]} max={years[years.length - 1]} step={1} value={year}
        onChange={e => { stop(); onChange(Number(e.target.value)) }}
        className="flex-1 accent-indigo-600" />
      <span className="font-mono text-sm font-semibold w-12 text-right">{year}</span>
    </div>
  )
}

// Compact year control: play · prev · dropdown · next (replaces the long slider)
export function YearStepper({ years, year, onChange, playable = true }) {
  const playing = useRef(false)
  const timer = useRef(null)
  const stop = () => { playing.current = false; if (timer.current) clearInterval(timer.current); timer.current = null }
  useEffect(() => stop, [])
  const i = years.indexOf(year)
  const go = (j) => { stop(); onChange(years[Math.max(0, Math.min(years.length - 1, j))]) }
  const togglePlay = () => {
    if (playing.current) { stop(); return }
    playing.current = true
    timer.current = setInterval(() => onChange(prev => {
      const k = years.indexOf(prev)
      return k >= years.length - 1 ? years[0] : years[k + 1]
    }), 650)
  }
  const btn = 'w-7 h-7 flex items-center justify-center rounded border border-slate-300 dark:border-slate-600 text-slate-500 hover:text-indigo-500 hover:border-indigo-400 disabled:opacity-30 disabled:hover:text-slate-500'
  return (
    <div className="flex items-center gap-1.5">
      {playable && (
        <button onClick={togglePlay} title="Play across years"
          className="w-7 h-7 flex items-center justify-center rounded bg-indigo-600 text-white text-xs hover:bg-indigo-500">▶</button>
      )}
      <button onClick={() => go(i - 1)} disabled={i <= 0} className={btn} title="Previous year">‹</button>
      <select value={year} onChange={e => { stop(); onChange(Number(e.target.value)) }}
        className="bg-transparent border border-slate-300 dark:border-slate-600 rounded px-2 py-1 text-sm font-mono font-semibold tabular-nums">
        {years.map(y => <option key={y} value={y}>{y}</option>)}
      </select>
      <button onClick={() => go(i + 1)} disabled={i >= years.length - 1} className={btn} title="Next year">›</button>
    </div>
  )
}

// `onBloc(region)` toggles a single regional-aggregate series ('@<Region>') in `selected`,
// replacing the old "select all members individually" — individual chips can still be mixed in
// (the bloc then excludes them, so nothing is double-counted).
export function CountryPicker({ countries, regionsOrder, selected, onToggle, onBloc, colorOf, query = '' }) {
  const q = query.trim().toLowerCase()
  const match = c => !q || c.iso3.toLowerCase().includes(q) || c.name.toLowerCase().includes(q)
  const byRegion = {}
  for (const c of countries) if (match(c)) (byRegion[c.region] ||= []).push(c)
  const regions = [...regionsOrder.filter(r => byRegion[r]),
                   ...Object.keys(byRegion).filter(r => !regionsOrder.includes(r))]
  return (
    <div className="space-y-2.5">
      {regions.map(region => {
        const list = byRegion[region]
        const sel = list.filter(c => selected.includes(c.iso3)).length
        const blocOn = selected.includes('@' + region)
        return (
          <div key={region} className="space-y-1">
            <div className="flex items-center justify-between gap-2">
              <div className="label truncate">{region}{' '}
                <span className="text-slate-400 normal-case font-normal">{sel}/{list.length}</span></div>
              {onBloc && (
                <button onClick={() => onBloc(region)} title={`Aggregate ${region} into one bloc`}
                  className={`shrink-0 text-[10px] px-1.5 py-0.5 rounded border inline-flex items-center gap-1 ${blocOn
                    ? 'bg-indigo-600 text-white border-indigo-600'
                    : 'text-slate-400 border-slate-400/40 hover:border-indigo-400 hover:text-indigo-400'}`}>
                  {blocOn && colorOf && <span className="w-1.5 h-1.5 rounded-full" style={{ background: colorOf('@' + region) }} />}
                  bloc
                </button>
              )}
            </div>
            <div className="flex flex-wrap gap-1">
              {list.map(c => {
                const on = selected.includes(c.iso3)
                return (
                  <button key={c.iso3} onClick={() => onToggle(c.iso3)} title={c.name}
                    className={`chip ${on ? 'chip-on' : 'chip-off'} ${blocOn && !on ? 'opacity-50' : ''}`}>
                    {on && colorOf && <span className="inline-block w-2 h-2 rounded-full mr-1 align-middle"
                      style={{ background: colorOf(c.iso3) }} />}
                    {c.iso3}
                  </button>
                )
              })}
            </div>
          </div>
        )
      })}
    </div>
  )
}

export function PciAxisLegend({ anchors }) {
  if (!anchors?.bins) return null
  const picks = anchors.bins.filter((_, i) => i % 3 === 0)
  return (
    <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500 dark:text-slate-400">
      <span className="label">Roughly at each PCI ({anchors.year}):</span>
      {picks.map(b => (
        <span key={b.pci}>
          <span className="font-mono">{fmtPci(b.pci)}</span>{' '}
          {b.products[0]?.chapter || '—'}
        </span>
      ))}
    </div>
  )
}
