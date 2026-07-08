import { useEffect, useState } from 'react'

const TABS = ['Hotspot Map', 'Ranked Works', 'Silent Needs']

export default function App() {
  const [tab, setTab] = useState(TABS[0])
  const [health, setHealth] = useState(null)
  const [demands, setDemands] = useState([])
  const [works, setWorks] = useState([])
  const [wards, setWards] = useState([])

  useEffect(() => {
    fetch('/api/health').then(r => r.json()).then(setHealth).catch(() => setHealth({ status: 'unreachable' }))
    fetch('/api/demands').then(r => r.json()).then(d => setDemands(d.demands || []))
    fetch('/api/works').then(r => r.json()).then(d => setWorks(d.works || []))
    fetch('/api/silent-needs').then(r => r.json()).then(d => setWards(d.wards || []))
  }, [])

  return (
    <>
      <header>
        <h1>sunwai</h1>
        <span>constituency demand intelligence</span>
        <span style={{ marginLeft: 'auto' }}>
          api: {health ? `${health.status} · db ${health.database ?? '?'}` : '…'}
        </span>
      </header>
      <nav>
        {TABS.map(t => (
          <button key={t} className={t === tab ? 'active' : ''} onClick={() => setTab(t)}>{t}</button>
        ))}
      </nav>
      <main>
        {tab === 'Hotspot Map' && (
          <>
            <p className="muted">Google Map with demand intensity lands in F3 — clustered demands below.</p>
            {demands.length === 0 && <div className="card muted">No demands yet. Inject one via POST /api/ingest/demo.</div>}
            {demands.map(d => (
              <div className="card" key={d.id}>
                <span className="pill">{d.category}</span>
                <strong>{d.title}</strong>
                <div className="muted">{d.signal_count} submissions{d.trend_7d ? ` · ${Math.round(d.trend_7d * 100)}%/wk` : ''}</div>
              </div>
            ))}
          </>
        )}
        {tab === 'Ranked Works' && (
          <>
            {works.length === 0 && <div className="card muted">Nothing ranked yet. POST /api/works/rerank after ingesting.</div>}
            {works.map(w => (
              <div className="card" key={w.id}>
                <strong>#{w.rank} — {w.title}</strong>
                <div className="muted">score {w.score?.toFixed(1)} · {w.signal_count} submissions</div>
                {w.justification && <p style={{ marginTop: 8 }}>{w.justification}</p>}
              </div>
            ))}
          </>
        )}
        {tab === 'Silent Needs' && (
          <>
            <p className="muted">Wards heard from least, alongside their indicators — unheard is not unneeding.</p>
            {wards.length === 0 && <div className="card muted">Load ward public data (F4) to activate this view.</div>}
            {wards.map(w => (
              <div className="card" key={w.ward_code}>
                <strong>{w.name}</strong>
                <div className="muted">{w.signals} submissions · population {w.population ?? '—'}</div>
              </div>
            ))}
          </>
        )}
      </main>
    </>
  )
}
