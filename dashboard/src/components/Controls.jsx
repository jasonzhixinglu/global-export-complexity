import { useEffect, useRef } from 'react'
import { colorFor, fmtPci } from '../lib/format.js'

export function MeasureToggle({ value, onChange, measures }) {
  return (
    <div className="seg">
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
    <div className="seg">
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
          className="shrink-0 w-8 h-8 flex items-center justify-center rounded-full bg-indigo-600 text-white text-xs hover:bg-indigo-500 transition-colors shadow-sm shadow-indigo-900/30"
          title="Play / pause across years">
          ▶
        </button>
      )}
      <span className="label hidden sm:block">Year</span>
      <input type="range" min={years[0]} max={years[years.length - 1]} step={1} value={year}
        onChange={e => { stop(); onChange(Number(e.target.value)) }}
        className="flex-1" />
      <span className="font-mono text-base font-semibold w-14 text-right tabular-nums">{year}</span>
    </div>
  )
}

export function CountryPicker({ countries, regionsOrder, selected, onToggle, colorByIso }) {
  const byRegion = {}
  for (const c of countries) (byRegion[c.region] ||= []).push(c)
  const regions = [...regionsOrder.filter(r => byRegion[r]),
                   ...Object.keys(byRegion).filter(r => !regionsOrder.includes(r))]
  return (
    <div className="space-y-2">
      {regions.map(region => (
        <div key={region} className="flex flex-wrap items-center gap-1.5">
          <span className="label w-24 shrink-0">{region}</span>
          {byRegion[region].map(c => {
            const on = selected.includes(c.iso3)
            return (
              <button key={c.iso3} onClick={() => onToggle(c.iso3)}
                className={`chip ${on ? 'chip-on' : 'chip-off'}`}>
                {on && <span className="inline-block w-2 h-2 rounded-full mr-1 align-middle"
                  style={{ background: colorFor(colorByIso[c.iso3]) }} />}
                {c.iso3}
              </button>
            )
          })}
        </div>
      ))}
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
