import { useCallback, useEffect, useState } from 'react'
import MapView from './MapView.jsx'

const TABS = ['Hotspot Map', 'Ranked Works', 'Silent Needs']
const POLL_MS = 10000

export default function App() {
  const [tab, setTab] = useState(TABS[0])
  const [health, setHealth] = useState(null)
  const [demands, setDemands] = useState([])
  const [works, setWorks] = useState([])
  const [wards, setWards] = useState([])
  const [selected, setSelected] = useState(null)

  const refresh = useCallback(() => {
    fetch('/api/health').then(r => r.json()).then(setHealth).catch(() => setHealth({ status: 'unreachable' }))
    fetch('/api/demands').then(r => r.json()).then(d => setDemands(d.demands || []))
    fetch('/api/works').then(r => r.json()).then(d => setWorks(d.works || []))
    fetch('/api/silent-needs').then(r => r.json()).then(d => setWards(d.wards || []))
  }, [])

  useEffect(() => {
    refresh()
    const id = setInterval(refresh, POLL_MS)
    return () => clearInterval(id)
  }, [refresh])

  const openDemand = useCallback(id => {
    fetch(`/api/demands/${id}`).then(r => r.json()).then(setSelected)
  }, [])

  const rerank = () => fetch('/api/works/rerank', { method: 'POST' }).then(refresh)

  return (
    <>
      <header>
        <h1>sunwai</h1>
        <span>South Delhi · constituency demand intelligence</span>
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
            <MapView demands={demands} onSelect={openDemand} />
            <div style={{ display: 'flex', gap: 14, marginTop: 14, alignItems: 'flex-start' }}>
              <div style={{ flex: 1 }}>
                {demands.length === 0 && <div className="card muted">No demands yet.</div>}
                {demands.map(d => (
                  <div className="card" key={d.id} onClick={() => openDemand(d.id)} style={{ cursor: 'pointer' }}>
                    <span className="pill">{d.category}</span>
                    <strong>{d.title}</strong>
                    <div className="muted">
                      {d.signal_count} submissions
                      {d.trend_7d ? ` · ${d.trend_7d > 0 ? '↑' : '↓'}${Math.abs(Math.round(d.trend_7d * 100))}%/wk` : ''}
                    </div>
                  </div>
                ))}
              </div>
              {selected?.demand && (
                <div className="card" style={{ flex: 1 }}>
                  <strong>{selected.demand.title}</strong>
                  <div className="muted">{selected.demand.signal_count} submissions</div>
                  <hr style={{ border: 'none', borderTop: '1px solid #e3e8f0', margin: '10px 0' }} />
                  {selected.sample_signals?.map((s, i) => (
                    <p key={i} style={{ marginBottom: 8 }}>
                      <span className="muted">[{s.kind}{s.language ? `, ${s.language}` : ''}]</span> {s.summary_en}
                    </p>
                  ))}
                  <button onClick={() => setSelected(null)}>close</button>
                </div>
              )}
            </div>
          </>
        )}
        {tab === 'Ranked Works' && (
          <>
            <button onClick={rerank} style={{ marginBottom: 12 }}>Recompute ranking</button>
            {works.length === 0 && <div className="card muted">Nothing ranked yet.</div>}
            {works.map(w => (
              <div className="card" key={w.id}>
                <strong>#{w.rank} — {w.title}</strong>
                <div className="muted">
                  score {w.score?.toFixed(1)} = {w.signal_count} submissions × trend × evidence
                </div>
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
