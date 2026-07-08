import { useCallback, useEffect, useState } from 'react'
import MapView from './MapView.jsx'
import PublicBoard from './PublicBoard.jsx'

const TABS = ['Hotspot Map', 'Ranked Works', 'Silent Needs']
const POLL_MS = 10000
const STATUS_LABEL = { open: 'Open', in_progress: 'In progress', resolved: 'Resolved' }

export default function App() {
  if (window.location.pathname.startsWith('/board')) return <PublicBoard />
  return <Dashboard />
}

function Dashboard() {
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
  }, [con])

  useEffect(() => {
    setSelected(null)
    refresh()
    const id = setInterval(refresh, POLL_MS)
    return () => clearInterval(id)
  }, [refresh])

  const openDemand = useCallback(id => {
    fetch(`/api/demands/${id}`).then(r => r.json()).then(setSelected)
  }, [])

  const rerank = () => fetch('/api/works/rerank', { method: 'POST' }).then(refresh)

  const setStatus = (id, status) =>
    fetch(`/api/demands/${id}/status`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ status }),
    }).then(refresh)

  const totalVoices = demands.reduce((n, d) => n + (d.signal_count || 0), 0)
  const wardsHeard = new Set(demands.map(d => d.ward_code).filter(Boolean)).size
  const conMeta = constituencies.find(x => x.code === con)

  return (
    <>
      <header>
        <div className="wordmark">
          <span className="dev">सुनवाई</span>
          <span className="latin">sunwai</span>
        </div>
        <span className="tagline">every voice, on the record</span>
        <label className="file-label">
          FILE /
          <select value={con} onChange={e => setCon(e.target.value)} aria-label="Constituency">
            {constituencies.map(x => (
              <option key={x.code} value={x.code}>{x.name}, {x.state}</option>
            ))}
          </select>
        </label>
        <span className="spacer" />
        <span className="api-status">
          api {health ? `${health.status} · db ${health.database ?? '?'}` : '…'}
        </span>
        <a className="btn-brief" href={`/api/brief?c=${con}`} target="_blank" rel="noreferrer">
          Export MP Brief
        </a>
      </header>

      <div className="record-strip">
        <span className="eyebrow"><span className="live-dot" /> <span className="dev">दर्ज</span> THE RECORD</span>
        <span><b>{totalVoices}</b> voices</span>
        <span><b>{wardsHeard}</b> wards heard</span>
        <span>{conMeta ? `${conMeta.name} PC, ${conMeta.state}` : ''}</span>
        <span className="spacer" style={{ marginLeft: 'auto' }}>
          <a href={`/board?c=${con}`} target="_blank" rel="noreferrer" style={{ color: 'var(--blue)' }}>
            public board ↗
          </a>
        </span>
      </div>

      <nav>
        {TABS.map(t => (
          <button key={t} className={t === tab ? 'active' : ''} onClick={() => setTab(t)}>{t}</button>
        ))}
      </nav>
      <main>
        {tab === 'Hotspot Map' && (
          <>
            <MapView demands={demands} onSelect={openDemand} center={conMeta} />
            <div className="two-col" style={{ display: 'flex', gap: 16, marginTop: 18, alignItems: 'flex-start' }}>
              <div style={{ flex: 1 }}>
                {demands.length === 0 && <div className="card muted">No demands on record yet.</div>}
                {demands.map(d => (
                  <div className="row" key={d.id} onClick={() => openDemand(d.id)} style={{ cursor: 'pointer' }}>
                    <span className="pill">{d.category}</span>
                    <strong>{d.title}</strong>
                    {d.status !== 'open' && <span className={`pill ${d.status === 'resolved' ? '' : 'pill-visit'}`} style={{ marginLeft: 8 }}>{STATUS_LABEL[d.status]}</span>}
                    <div className="fact" style={{ marginTop: 4 }}>
                      {d.signal_count} submissions
                      {d.trend_7d ? ` · ${d.trend_7d > 0 ? '↑' : '↓'}${Math.abs(Math.round(d.trend_7d * 100))}%/wk` : ''}
                    </div>
                  </div>
                ))}
              </div>
              {selected?.demand && (
                <div className="card" style={{ flex: 1, position: 'sticky', top: 12 }}>
                  <strong>{selected.demand.title}</strong>
                  <div className="fact">{selected.demand.signal_count} submissions on record</div>
                  <hr style={{ border: 'none', borderTop: '1px solid var(--rule)', margin: '10px 0' }} />
                  {selected.sample_signals?.map((s, i) => (
                    <p key={i} style={{ marginBottom: 8, fontSize: 14 }}>
                      <span className="fact">[{s.kind}{s.language ? `, ${s.language}` : ''}]</span> {s.summary_en}
                    </p>
                  ))}
                  <button className="plain" onClick={() => setSelected(null)}>close</button>
                </div>
              )}
            </div>
          </>
        )}
        {tab === 'Ranked Works' && (
          <>
            <button className="action" onClick={rerank} style={{ marginBottom: 14 }}>Recompute ranking</button>
            {works.length === 0 && <div className="card muted">Nothing ranked yet.</div>}
            {works.map(w => (
              <div className="row" key={w.id}>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, flexWrap: 'wrap' }}>
                  {w.rank === 1
                    ? <span className="stamp">№ 1</span>
                    : <span className="rank-no">№ {w.rank}</span>}
                  <strong>{w.title}</strong>
                  <span className="pill">{w.category}</span>
                  <span className="spacer" style={{ marginLeft: 'auto' }} />
                  <select className="fact" value={w.status || 'open'}
                          onChange={e => setStatus(w.id, e.target.value)}
                          aria-label={`Status of ${w.title}`}>
                    {Object.entries(STATUS_LABEL).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                  </select>
                </div>
                <div className="fact" style={{ marginTop: 6 }}>
                  score {w.score?.toFixed(1)} = {w.signal_count} submissions
                  × {(1 + (w.trend_7d || 0)).toFixed(2)} trend
                  × {(w.evidence?.gap_weight ?? 1).toFixed(2)} evidence gap
                </div>
                {w.evidence?.facts?.length > 0 && (
                  <ul className="facts">
                    {w.evidence.facts.map((f, i) => <li key={i}>{f}</li>)}
                  </ul>
                )}
                {w.justification && <p className="justification">{w.justification}</p>}
              </div>
            ))}
          </>
        )}
        {tab === 'Silent Needs' && (
          <>
            <p className="muted" style={{ marginBottom: 14 }}>
              silence = need × (1 − voice): high-need wards that submit least are likely
              unheard, not unneeding. Wards under 30k population excluded.
            </p>
            {wards.length === 0 && <div className="card muted">Load ward public data to activate this view.</div>}
            {wards.map(w => (
              <div className="row" key={w.ward_code}>
                <strong>{w.name}</strong>
                {w.suggest_visit && <span className="pill pill-visit" style={{ marginLeft: 8 }}>suggest field visit</span>}
                <div className="fact" style={{ marginTop: 4 }}>
                  silence {w.silence_score?.toFixed(2)} · {w.signals} submissions · population {w.population?.toLocaleString()}
                </div>
                {w.facts && (
                  <ul className="facts">
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
