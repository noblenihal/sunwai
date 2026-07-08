import { useCallback, useEffect, useState } from 'react'
import Landing from './Landing.jsx'
import MapView from './MapView.jsx'
import PublicBoard from './PublicBoard.jsx'

const TABS = ['Hotspot Map', 'Ranked Works', 'Silent Needs']
const POLL_MS = 10000
const STATUS_LABEL = { open: 'Open', in_progress: 'In progress', resolved: 'Resolved' }

export default function App() {
  const path = window.location.pathname
  if (path.startsWith('/board')) return <PublicBoard />
  if (path.startsWith('/app')) return <Dashboard />
  return <Landing />
}

const CATEGORIES = ['road', 'water', 'school', 'health', 'drainage', 'electricity', 'other']

function RankingSettings({ con, onSaved }) {
  const [open, setOpen] = useState(false)
  const [cfg, setCfg] = useState(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (open) fetch(`/api/ranking-config?c=${con}`).then(r => r.json()).then(setCfg)
  }, [open, con])

  const save = () => {
    setSaving(true)
    fetch(`/api/ranking-config?c=${con}`, {
      method: 'PUT',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(cfg),
    }).then(() => { setSaving(false); setOpen(false); onSaved() })
  }

  return (
    <>
      <button className="plain" onClick={() => setOpen(!open)}>⚙ Ranking parameters</button>
      {open && cfg && (
        <div className="card" style={{ position: 'absolute', zIndex: 30, marginTop: 42, maxWidth: 560, boxShadow: 'var(--shadow-2)' }}>
          <strong>How this office ranks demands</strong>
          <p className="muted" style={{ margin: '4px 0 14px' }}>
            The formula stays visible on every work — these controls change its weights.
          </p>
          <label className="muted" style={{ display: 'block', marginBottom: 10 }}>
            Momentum matters ({cfg.trend_weight.toFixed(1)}×)
            <input type="range" min="0" max="2" step="0.1" value={cfg.trend_weight}
                   style={{ width: '100%' }}
                   onChange={e => setCfg({ ...cfg, trend_weight: +e.target.value })} />
          </label>
          <label className="muted" style={{ display: 'block', marginBottom: 12 }}>
            Evidence gap matters ({cfg.evidence_weight.toFixed(1)}×)
            <input type="range" min="0" max="2" step="0.1" value={cfg.evidence_weight}
                   style={{ width: '100%' }}
                   onChange={e => setCfg({ ...cfg, evidence_weight: +e.target.value })} />
          </label>
          <div className="muted" style={{ marginBottom: 6 }}>Category boosts (0.5–2×)</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 14 }}>
            {CATEGORIES.map(cat => (
              <label key={cat} className="fact" style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                {cat}
                <input type="number" min="0.5" max="2" step="0.1"
                       value={cfg.category_boosts?.[cat] ?? 1}
                       style={{ width: 54, padding: '3px 6px', border: '1px solid var(--rule)', borderRadius: 6 }}
                       onChange={e => setCfg({ ...cfg, category_boosts: { ...cfg.category_boosts, [cat]: +e.target.value } })} />
              </label>
            ))}
          </div>
          <label className="muted" style={{ display: 'block', marginBottom: 14 }}>
            Office priorities, in plain language — the AI weighs each demand against these
            <textarea rows={3} value={cfg.directives} maxLength={1000}
                      placeholder="e.g. Water issues first before summer peak. Anything affecting school children is urgent."
                      style={{ width: '100%', marginTop: 6, padding: 10, border: '1px solid var(--rule)', borderRadius: 8, fontFamily: 'inherit', fontSize: 13.5 }}
                      onChange={e => setCfg({ ...cfg, directives: e.target.value })} />
          </label>
          <div style={{ display: 'flex', gap: 10 }}>
            <button className="action" onClick={save} disabled={saving}>
              {saving ? 'Saving & reranking…' : 'Save & rerank'}
            </button>
            <button className="plain" onClick={() => setOpen(false)}>Cancel</button>
          </div>
        </div>
      )}
    </>
  )
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
                    {d.status !== 'open' && <span className={`pill ${d.status === 'resolved' ? 'pill-done' : 'pill-visit'}`} style={{ marginLeft: 8 }}>{STATUS_LABEL[d.status]}</span>}
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
            <div style={{ display: 'flex', gap: 10, marginBottom: 14 }}>
              <button className="action" onClick={rerank}>Recompute ranking</button>
              <RankingSettings con={con} onSaved={refresh} />
            </div>
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
                  × {(1 + (w.evidence?.trend_weight ?? 1) * (w.trend_7d || 0)).toFixed(2)} trend
                  × {(1 + (w.evidence?.evidence_weight ?? 1) * ((w.evidence?.gap_weight ?? 1) - 1)).toFixed(2)} evidence
                  {w.evidence?.category_boost && w.evidence.category_boost !== 1 ? ` × ${w.evidence.category_boost.toFixed(2)} ${w.category} boost` : ''}
                  {w.evidence?.directive_modifier && w.evidence.directive_modifier !== 1 ? ` × ${w.evidence.directive_modifier.toFixed(2)} office priority` : ''}
                </div>
                {w.evidence?.directive_note && (
                  <div className="fact" style={{ marginTop: 4, color: 'var(--blue)' }}>
                    ⚙ {w.evidence.directive_note}
                  </div>
                )}
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
