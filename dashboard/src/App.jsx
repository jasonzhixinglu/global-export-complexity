import { useDataset } from './lib/data.js'
import { useSessionState } from './lib/sessionState.js'
import { useDarkMode } from './lib/useDarkMode.jsx'
import ExplorerPanel from './components/ExplorerPanel.jsx'
import TechPanel from './components/TechPanel.jsx'
import SegmentPanel from './components/SegmentPanel.jsx'
import CountryPanel from './components/CountryPanel.jsx'
import AboutPanel from './components/AboutPanel.jsx'

const TABS = [
  { id: 'explorer', label: 'Explorer', sub: 'Distribution across complexity' },
  { id: 'tech', label: 'Tech & AI', sub: 'AI compute · semiconductors' },
  { id: 'segment', label: 'Segment', sub: 'A complexity band across countries' },
  { id: 'country', label: 'Country', sub: 'Single-country deep dive' },
  { id: 'about', label: 'Coverage · About', sub: 'Coverage · Methodology' },
]

function SunIcon() {
  return (<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="5" /><line x1="12" y1="1" x2="12" y2="3" /><line x1="12" y1="21" x2="12" y2="23" /><line x1="4.22" y1="4.22" x2="5.64" y2="5.64" /><line x1="18.36" y1="18.36" x2="19.78" y2="19.78" /><line x1="1" y1="12" x2="3" y2="12" /><line x1="21" y1="12" x2="23" y2="12" /><line x1="4.22" y1="19.78" x2="5.64" y2="18.36" /><line x1="18.36" y1="5.64" x2="19.78" y2="4.22" /></svg>)
}
function MoonIcon() {
  return (<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" /></svg>)
}

export default function App() {
  const { data, error } = useDataset()
  const { isDark, toggle } = useDarkMode()
  const [tab, setTab] = useSessionState('gec-tab', 'explorer')
  const [selected, setSelected] = useSessionState('gec-selected', ['CHN', 'DEU', 'JPN', 'USA'])
  const [year, setYear] = useSessionState('gec-year', 2024)
  const [measure, setMeasure] = useSessionState('gec-measure', 'share')

  return (
    <div className="flex flex-col min-h-screen">
      <header className="border-b border-slate-200 dark:border-slate-800 px-4 sm:px-6 py-3">
        <div className="max-w-screen-2xl mx-auto flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
          <div className="min-w-0">
            <h1 className="text-base font-semibold leading-tight">Global Export Complexity</h1>
            <p className="text-xs text-slate-500 mt-0.5">
              Exports across the Product Complexity Index · 2000–2024 · Atlas of Economic Complexity
            </p>
          </div>
          <div className="flex items-start gap-2 flex-shrink-0">
            <nav className="grid grid-cols-2 gap-1.5 sm:flex sm:flex-wrap">
              {TABS.map(t => (
                <button key={t.id} onClick={() => setTab(t.id)}
                  className={`tab-btn text-left ${tab === t.id ? 'tab-btn-active' : 'tab-btn-inactive'}`}>
                  <div>{t.label}</div>
                  <div className={`text-xs mt-0.5 font-normal hidden lg:block ${tab === t.id ? 'text-indigo-200' : 'text-slate-400 dark:text-slate-600'}`}>{t.sub}</div>
                </button>
              ))}
            </nav>
            <button onClick={toggle} className="shrink-0 p-2 rounded-lg text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800" aria-label="Toggle theme">
              {isDark ? <SunIcon /> : <MoonIcon />}
            </button>
          </div>
        </div>
      </header>

      <main className="flex-1 px-4 sm:px-6 py-5">
        <div className="max-w-screen-2xl mx-auto">
          {error && <div className="panel p-6 text-sm text-rose-500">Failed to load data: {String(error.message || error)}</div>}
          {!data && !error && <div className="panel p-10 text-center text-slate-400">Loading data…</div>}
          {data && tab === 'explorer' && (
            <ExplorerPanel data={data} selected={selected} setSelected={setSelected}
              year={year} setYear={setYear} measure={measure} setMeasure={setMeasure} />
          )}
          {data && tab === 'tech' && (
            <TechPanel data={data} year={year} setYear={setYear} measure={measure} setMeasure={setMeasure} />
          )}
          {data && tab === 'segment' && (
            <SegmentPanel data={data} year={year} setYear={setYear} measure={measure} setMeasure={setMeasure} />
          )}
          {data && tab === 'country' && (
            <CountryPanel data={data} year={year} setYear={setYear} measure={measure} setMeasure={setMeasure} />
          )}
          {data && tab === 'about' && (
            <AboutPanel data={data} year={year} setYear={setYear} />
          )}
        </div>
      </main>

      <footer className="border-t border-slate-200 dark:border-slate-800 px-6 py-3 text-xs text-slate-400">
        Data: Harvard Growth Lab, Atlas of Economic Complexity (HS92). Built from the project pipeline.
      </footer>
    </div>
  )
}
