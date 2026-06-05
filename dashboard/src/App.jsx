import { useDataset, MEASURES } from './lib/data.js'
import { useSessionState } from './lib/sessionState.js'
import { useDarkMode } from './lib/useDarkMode.jsx'
import { MeasureToggle, YearSlider } from './components/Controls.jsx'
import ExplorerPanel from './components/ExplorerPanel.jsx'
import TechPanel from './components/TechPanel.jsx'
import SegmentPanel from './components/SegmentPanel.jsx'
import CountryPanel from './components/CountryPanel.jsx'
import AboutPanel from './components/AboutPanel.jsx'

const SECTIONS = [
  { id: 'explorer', label: 'Explorer', desc: 'Distribution of exports across product complexity' },
  { id: 'tech', label: 'Tech & AI', desc: 'AI-compute and semiconductor value-chain exports' },
  { id: 'segment', label: 'Segment', desc: 'A complexity band, ranked across countries' },
  { id: 'country', label: 'Country', desc: 'Single-country deep dive' },
  { id: 'coverage', label: 'Coverage', desc: 'Top-N coverage by complexity · methodology' },
]

function SunIcon() {
  return (<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="5" /><line x1="12" y1="1" x2="12" y2="3" /><line x1="12" y1="21" x2="12" y2="23" /><line x1="4.22" y1="4.22" x2="5.64" y2="5.64" /><line x1="18.36" y1="18.36" x2="19.78" y2="19.78" /><line x1="1" y1="12" x2="3" y2="12" /><line x1="21" y1="12" x2="23" y2="12" /><line x1="4.22" y1="19.78" x2="5.64" y2="18.36" /><line x1="18.36" y1="5.64" x2="19.78" y2="4.22" /></svg>)
}
function MoonIcon() {
  return (<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" /></svg>)
}

function scrollTo(id) {
  const el = document.getElementById(id)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function Section({ id, label, desc, children }) {
  return (
    <section id={id} className="scroll-mt-32 space-y-2">
      <div className="flex items-baseline gap-3 border-b border-slate-200 dark:border-slate-800 pb-1.5">
        <h2 className="text-sm font-semibold text-slate-800 dark:text-slate-100">{label}</h2>
        <span className="text-xs text-slate-400">{desc}</span>
      </div>
      {children}
    </section>
  )
}

export default function App() {
  const { data, error } = useDataset()
  const { isDark, toggle } = useDarkMode()
  const [selected, setSelected] = useSessionState('gec-selected', ['CHN', 'DEU', 'JPN', 'USA'])
  const [year, setYear] = useSessionState('gec-year', 2024)
  const [measure, setMeasure] = useSessionState('gec-measure', 'share')

  return (
    <div className="flex flex-col min-h-screen">
      <div className="sticky top-0 z-20 bg-slate-50/90 dark:bg-slate-950/90 backdrop-blur border-b border-slate-200 dark:border-slate-800">
        <div className="max-w-screen-2xl mx-auto px-4 sm:px-6">
          {/* title + section nav */}
          <div className="flex items-center justify-between gap-4 py-2.5">
            <div className="min-w-0">
              <h1 className="text-[15px] font-semibold leading-tight">Global Export Complexity</h1>
              <p className="text-[11px] text-slate-500 leading-tight">Exports across the Product Complexity Index · 2000–2024 · Atlas of Economic Complexity</p>
            </div>
            <nav className="hidden md:flex items-center gap-1">
              {SECTIONS.map(s => (
                <button key={s.id} onClick={() => scrollTo(s.id)} className="tab-btn tab-btn-inactive">{s.label}</button>
              ))}
            </nav>
            <button onClick={toggle} className="shrink-0 p-2 rounded text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800" aria-label="Toggle theme">
              {isDark ? <SunIcon /> : <MoonIcon />}
            </button>
          </div>
          {/* shared control bar */}
          <div className="flex flex-wrap items-center gap-x-5 gap-y-2 py-2 border-t border-slate-200/70 dark:border-slate-800/70">
            <div className="flex items-center gap-2">
              <span className="label">Measure</span>
              <MeasureToggle value={measure} onChange={setMeasure} measures={MEASURES} />
            </div>
            <div className="flex items-center gap-2 flex-1 min-w-[260px]">
              <YearSlider years={data?.meta.years || [2000, 2024]} year={year} onChange={setYear} />
            </div>
          </div>
        </div>
      </div>

      <main className="flex-1 px-4 sm:px-6 py-5">
        <div className="max-w-screen-2xl mx-auto space-y-8">
          {error && <div className="panel p-6 text-sm text-rose-500">Failed to load data: {String(error.message || error)}</div>}
          {!data && !error && <div className="panel p-10 text-center text-slate-400">Loading data…</div>}
          {data && (
            <>
              <Section {...SECTIONS[0]}>
                <ExplorerPanel data={data} selected={selected} setSelected={setSelected} year={year} measure={measure} />
              </Section>
              <Section {...SECTIONS[1]}>
                <TechPanel data={data} year={year} measure={measure} />
              </Section>
              <Section {...SECTIONS[2]}>
                <SegmentPanel data={data} year={year} measure={measure} />
              </Section>
              <Section {...SECTIONS[3]}>
                <CountryPanel data={data} year={year} measure={measure} />
              </Section>
              <Section {...SECTIONS[4]}>
                <AboutPanel data={data} year={year} />
              </Section>
            </>
          )}
        </div>
      </main>

      <footer className="border-t border-slate-200 dark:border-slate-800 px-6 py-3 text-xs text-slate-400">
        Data: Harvard Growth Lab, Atlas of Economic Complexity (HS92 · HS12). Built from the project pipeline.
      </footer>
    </div>
  )
}
