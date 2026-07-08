import { useCallback, useEffect, useState } from 'react'
import Landing from './Landing.jsx'
import MapView from './MapView.jsx'
import PublicBoard from './PublicBoard.jsx'

const TABS = ['Hotspot Map', 'Ranked Works', 'Silent Needs']
const POLL_MS = 10000
const STATUS_LABEL = { open: 'Open', in_progress: 'In progress', resolved: 'Resolved' }
const CATEGORIES = ['road', 'water', 'school', 'health', 'drainage', 'electricity', 'other']

export default function App() {
  const path = window.location.pathname
  if (path.startsWith('/board')) return <PublicBoard />
  if (path.startsWith('/app')) return <Dashboard />
  return <Landing />
}

function DemandPanel({ selected, onClose }) {
  const [origAll, setOrigAll] = useState(false)
  const [origOne, setOrigOne] = useState({})

  useEffect(() => { setOrigAll(false); setOrigOne({}) }, [selected?.demand?.id])

  const isOrig = i => origOne[i] ?? origAll
  const hasOriginals = selected.sample_signals?.some(s => s.original)

  return (
    <div className="glass-panel sticky-panel slide-in-right">
      <div className="panel-header">
        <h3 className="panel-title">{selected.demand.title}</h3>
        {hasOriginals && (
          <button className="btn-text" onClick={() => { setOrigAll(!origAll); setOrigOne({}) }}>
            {origAll ? 'View Summaries' : 'View Originals'}
          </button>
        )}
      </div>
      <div className="metric-badge">
        <span className="metric-val">{selected.demand.signal_count}</span>
        <span className="metric-lbl">submissions on record</span>
      </div>
      
      <div className="signal-list">
        {selected.sample_signals?.map((s, i) => (
          <div key={i} className="signal-item">
            <div className="signal-meta">[{s.kind}{s.language ? `, ${s.language}` : ''}]</div>
            <div className="signal-text">
              {isOrig(i) && s.original ? <span lang="und">{s.original}</span> : s.summary_en}
            </div>
            {s.original && (
              <button className="btn-text btn-small" onClick={() => setOrigOne({ ...origOne, [i]: !isOrig(i) })}>
                {isOrig(i) ? 'Show Summary' : 'Show Original'}
              </button>
            )}
          </div>
        ))}
      </div>
      <button className="btn-secondary w-full mt-4" onClick={onClose}>Close Panel</button>
    </div>
  )
}

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
    <div className="settings-wrapper">
      <button className="btn-secondary" onClick={() => setOpen(!open)}>
        <span className="icon">⚙</span> Ranking Parameters
      </button>
      {open && cfg && (
        <div className="glass-modal pop-in">
          <h3 className="modal-title">How this office ranks demands</h3>
          <p className="modal-desc">Adjust weights below. The formula stays visible on every work.</p>
          
          <div className="slider-group">
            <label>Momentum matters ({cfg.trend_weight.toFixed(1)}×)</label>
            <input type="range" min="0" max="2" step="0.1" value={cfg.trend_weight}
                   onChange={e => setCfg({ ...cfg, trend_weight: +e.target.value })} />
          </div>
          
          <div className="slider-group">
            <label>Evidence gap matters ({cfg.evidence_weight.toFixed(1)}×)</label>
            <input type="range" min="0" max="2" step="0.1" value={cfg.evidence_weight}
                   onChange={e => setCfg({ ...cfg, evidence_weight: +e.target.value })} />
          </div>
          
          <div className="category-boosts">
            <label>Category boosts (0.5–2×)</label>
            <div className="boost-grid">
              {CATEGORIES.map(cat => (
                <div key={cat} className="boost-item">
                  <span>{cat}</span>
                  <input type="number" min="0.5" max="2" step="0.1"
                         value={cfg.category_boosts?.[cat] ?? 1}
                         onChange={e => setCfg({ ...cfg, category_boosts: { ...cfg.category_boosts, [cat]: +e.target.value } })} />
                </div>
              ))}
            </div>
          </div>
          
          <div className="textarea-group">
            <label>Office priorities (Plain language directives)</label>
            <textarea rows={3} value={cfg.directives} maxLength={1000}
                      placeholder="e.g. Water issues first before summer peak."
                      onChange={e => setCfg({ ...cfg, directives: e.target.value })} />
          </div>
          
          <div className="modal-actions">
            <button className="btn-primary" onClick={save} disabled={saving}>
              {saving ? 'Saving...' : 'Save & Rerank'}
            </button>
            <button className="btn-text" onClick={() => setOpen(false)}>Cancel</button>
          </div>
        </div>
      )}
    </div>
  )
}

function ScoreBar({ score, maxScore = 100 }) {
  const pct = Math.min(100, Math.max(0, (score / maxScore) * 100))
  return (
    <div className="score-bar-bg">
      <div className="score-bar-fill" style={{ width: `${pct}%` }}></div>
    </div>
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
  
  // Find max score for progress bars
  const maxScore = works.reduce((max, w) => Math.max(max, w.score || 0), 10)

  return (
    <div className="app-shell">
      {/* Top Navigation */}
      <header className="app-topbar">
        <div className="brand-group">
          <img src="/logo.png" alt="Sunwai Logo" className="app-logo" />
          <span className="brand-name">Sunwai</span>
        </div>
        
        <div className="context-selector">
          <span className="lbl">FILE /</span>
          <select className="select-modern" value={con} onChange={e => setCon(e.target.value)}>
            {constituencies.map(x => (
              <option key={x.code} value={x.code}>{x.name}, {x.state}</option>
            ))}
          </select>
        </div>
        
        <div className="topbar-actions">
          <span className="status-indicator">
            <span className={`dot ${health?.status === 'ok' ? 'ok' : 'err'}`}></span>
            API {health?.status || '...'}
          </span>
          <a className="btn-secondary" href={`/api/brief?c=${con}`} target="_blank" rel="noreferrer">
            Export Brief
          </a>
        </div>
      </header>

      {/* Main Dashboard Layout */}
      <div className="dashboard-layout">
        {/* Sidebar Nav */}
        <aside className="dashboard-sidebar">
          <div className="sidebar-stats">
            <div className="stat-box">
              <span className="val">{totalVoices}</span>
              <span className="lbl">Voices</span>
            </div>
            <div className="stat-box">
              <span className="val">{wardsHeard}</span>
              <span className="lbl">Wards</span>
            </div>
          </div>
          
          <nav className="sidebar-nav">
            {TABS.map(t => (
              <button key={t} className={`nav-item ${t === tab ? 'active' : ''}`} onClick={() => setTab(t)}>
                {t}
              </button>
            ))}
          </nav>
          
          <div className="sidebar-footer">
            <a href={`/board?c=${con}`} target="_blank" rel="noreferrer" className="link-external">
              Public Board ↗
            </a>
          </div>
        </aside>

        {/* Main Content Area */}
        <main className="dashboard-content fade-in">
          {tab === 'Hotspot Map' && (
            <div className="view-map">
              <div className="map-container">
                <MapView demands={demands} onSelect={openDemand} center={conMeta} />
              </div>
              <div className="map-split">
                <div className="demands-list">
                  {demands.length === 0 && <div className="empty-state">No demands on record yet.</div>}
                  {demands.map((d, i) => (
                    <div className="data-card hover-lift" key={d.id} onClick={() => openDemand(d.id)} style={{ animationDelay: `${i * 0.05}s` }}>
                      <div className="card-header">
                        <span className={`badge badge-${d.category}`}>{d.category}</span>
                        {d.status !== 'open' && <span className={`badge badge-${d.status}`}>{STATUS_LABEL[d.status]}</span>}
                      </div>
                      <h4 className="card-title">{d.title}</h4>
                      <div className="card-metrics">
                        <span>{d.signal_count} submissions</span>
                        {d.trend_7d ? <span className={`trend ${d.trend_7d > 0 ? 'up' : 'down'}`}>
                          {d.trend_7d > 0 ? '↑' : '↓'} {Math.abs(Math.round(d.trend_7d * 100))}%/wk
                        </span> : null}
                      </div>
                    </div>
                  ))}
                </div>
                <div className="demand-detail">
                  {selected?.demand ? (
                    <DemandPanel selected={selected} onClose={() => setSelected(null)} />
                  ) : (
                    <div className="empty-panel">Select a demand to view evidence</div>
                  )}
                </div>
              </div>
            </div>
          )}

          {tab === 'Ranked Works' && (
            <div className="view-ranked">
              <div className="view-toolbar">
                <button className="btn-primary" onClick={rerank}>Recompute Ranking</button>
                <RankingSettings con={con} onSaved={refresh} />
              </div>
              
              <div className="works-list">
                {works.length === 0 && <div className="empty-state">Nothing ranked yet.</div>}
                {works.map((w, i) => (
                  <div className="work-card stagger-item" key={w.id} style={{ animationDelay: `${i * 0.05}s` }}>
                    <div className="work-header">
                      <div className="rank-badge">
                        {w.rank === 1 ? '🥇 No. 1' : `#${w.rank}`}
                      </div>
                      <h4 className="work-title">{w.title}</h4>
                      <span className={`badge badge-${w.category}`}>{w.category}</span>
                      
                      <div className="work-actions">
                        <select className="select-status" value={w.status || 'open'}
                                onChange={e => setStatus(w.id, e.target.value)}>
                          {Object.entries(STATUS_LABEL).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                        </select>
                      </div>
                    </div>
                    
                    <div className="work-score-section">
                      <div className="score-header">
                        <span className="score-lbl">Priority Score: {w.score?.toFixed(1)}</span>
                        <span className="score-math">
                          {w.signal_count} sigs × {(1 + (w.evidence?.trend_weight ?? 1) * (w.trend_7d || 0)).toFixed(2)} trend × {(1 + (w.evidence?.evidence_weight ?? 1) * ((w.evidence?.gap_weight ?? 1) - 1)).toFixed(2)} gap
                        </span>
                      </div>
                      <ScoreBar score={w.score} maxScore={maxScore} />
                    </div>

                    <div className="work-evidence">
                      {w.evidence?.directive_note && (
                        <div className="directive-note">⚙ {w.evidence.directive_note}</div>
                      )}
                      {w.evidence?.facts?.length > 0 && (
                        <ul className="fact-list">
                          {w.evidence.facts.map((f, idx) => <li key={idx}>{f}</li>)}
                        </ul>
                      )}
                    </div>
                    
                    {w.justification && (
                      <div className="ai-justification">
                        <span className="ai-icon">✨</span>
                        <p>{w.justification}</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {tab === 'Silent Needs' && (
            <div className="view-silent">
              <div className="alert-banner">
                <span className="icon">🚨</span>
                <p><strong>Silence = Need × (1 − Voice).</strong> High-need wards that submit least are likely unheard, not unneeding. Wards under 30k population excluded.</p>
              </div>
              
              <div className="wards-grid">
                {wards.length === 0 && <div className="empty-state">Load ward public data to activate this view.</div>}
                {wards.map((w, i) => (
                  <div className="ward-card stagger-item" key={w.ward_code} style={{ animationDelay: `${i * 0.05}s` }}>
                    <div className="ward-header">
                      <h4 className="ward-name">{w.name}</h4>
                      {w.suggest_visit && <span className="badge badge-urgent">Suggest Field Visit</span>}
                    </div>
                    
                    <div className="ward-stats">
                      <div className="stat">
                        <span className="val">{w.silence_score?.toFixed(2)}</span>
                        <span className="lbl">Silence Score</span>
                      </div>
                      <div className="stat">
                        <span className="val">{w.signals}</span>
                        <span className="lbl">Submissions</span>
                      </div>
                      <div className="stat">
                        <span className="val">{w.population?.toLocaleString()}</span>
                        <span className="lbl">Population</span>
                      </div>
                    </div>
                    
                    {w.facts && (
                      <ul className="fact-list mt-3">
                        {w.facts.map((f, idx) => <li key={idx}>{f}</li>)}
                      </ul>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
