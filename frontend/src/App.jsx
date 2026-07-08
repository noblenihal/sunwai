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
  const [constituencies, setConstituencies] = useState([])
  const [con, setCon] = useState('south-delhi')

  useEffect(() => {
    fetch('/api/constituencies').then(r => r.json()).then(d => setConstituencies(d.constituencies || []))
  }, [])

  const refresh = useCallback(() => {
    fetch('/api/health').then(r => r.json()).then(setHealth).catch(() => setHealth({ status: 'unreachable' }))
    fetch(`/api/demands?c=${con}`).then(r => r.json()).then(d => setDemands(d.demands || []))
    fetch(`/api/works?c=${con}`).then(r => r.json()).then(d => setWorks(d.works || []))
    fetch(`/api/silent-needs?c=${con}`).then(r => r.json()).then(d => setWards(d.wards || []))
    setSelected(null)
  }, [con])

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
        <select value={con} onChange={e => setCon(e.target.value)}
                style={{ padding: '6px 10px', borderRadius: 8, border: '1px solid #d6deea', fontSize: 14 }}>
          {constituencies.map(x => (
            <option key={x.code} value={x.code}>{x.name}, {x.state}</option>
          ))}
        </select>
        <span>constituency demand intelligence</span>
        <span style={{ marginLeft: 'auto' }}>
          api: {health ? `${health.status} · db ${health.database ?? '?'}` : '…'}
        </span>
        <a href={`/api/brief?c=${con}`} target="_blank" rel="noreferrer"
           style={{ background: '#1a53ff', color: '#fff', padding: '7px 14px', borderRadius: 8, fontSize: 13, textDecoration: 'none' }}>
          Export MP Brief
        </a>
      </header>
      <nav>
        {TABS.map(t => (
          <button key={t} className={t === tab ? 'active' : ''} onClick={() => setTab(t)}>{t}</button>
        ))}
      </nav>
      <main>
        {tab === 'Hotspot Map' && (
          <>
            <MapView demands={demands} onSelect={openDemand}
                     center={constituencies.find(x => x.code === con)} />
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
                  score {w.score?.toFixed(1)} = {w.signal_count} submissions
                  × {(1 + (w.trend_7d || 0)).toFixed(2)} trend
                  × {(w.evidence?.gap_weight ?? 1).toFixed(2)} evidence gap
                </div>
                {w.evidence?.facts?.length > 0 && (
                  <ul className="muted" style={{ margin: '8px 0 0 18px' }}>
                    {w.evidence.facts.map((f, i) => <li key={i}>{f}</li>)}
                  </ul>
                )}
                {w.justification && <p style={{ marginTop: 8 }}>{w.justification}</p>}
              </div>
            ))}
          </>
        )}
        {tab === 'Silent Needs' && (
          <>
            <p className="muted">
              silence = need × (1 − voice): high-need wards that submit least are likely
              unheard, not unneeding. Wards under 30k population excluded.
            </p>
            {wards.length === 0 && <div className="card muted">Load ward public data (F4) to activate this view.</div>}
            {wards.map(w => (
              <div className="card" key={w.ward_code}>
                <strong>{w.name}</strong>
                {w.suggest_visit && <span className="pill" style={{ marginLeft: 8, background: '#fff3e8', color: '#c05717' }}>suggest field visit</span>}
                <div className="muted">silence score {w.silence_score?.toFixed(2)} · {w.signals} submissions · population {w.population?.toLocaleString()}</div>
                {w.facts && (
                  <ul className="muted" style={{ margin: '8px 0 0 18px' }}>
                    {w.facts.map((f, i) => <li key={i}>{f}</li>)}
                  </ul>
                )}
              </div>
            ))}
          </>
        )}
      </main>
    </>
  )
}
