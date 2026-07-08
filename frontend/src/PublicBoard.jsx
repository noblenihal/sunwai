import { useEffect, useState } from 'react'

export default function PublicBoard() {
  const params = new URLSearchParams(window.location.search)
  const [con, setCon] = useState(params.get('c') || 'south-delhi')
  const [constituencies, setConstituencies] = useState([])
  const [board, setBoard] = useState({ open: [], resolved: [] })

  useEffect(() => {
    fetch('/api/constituencies').then(r => r.json()).then(d => setConstituencies(d.constituencies || []))
  }, [])

  useEffect(() => {
    fetch(`/api/public/board?c=${con}`).then(r => r.json()).then(setBoard)
  }, [con])

  const conMeta = constituencies.find(x => x.code === con)

  return (
    <div className="public-board-page">
      <header className="pb-header glass-panel">
        <div className="brand-group">
          <img src="/logo.png" alt="Sunwai Logo" className="app-logo" />
          <span className="brand-name">Sunwai</span>
        </div>
        <div className="pb-context">
          <span className="lbl">Public Record for</span>
          <select className="select-modern" value={con} onChange={e => setCon(e.target.value)}>
            {constituencies.map(x => (
              <option key={x.code} value={x.code}>{x.name}, {x.state}</option>
            ))}
          </select>
        </div>
      </header>

      <div className="pb-hero stagger-1">
        <h1>Civic Transparency Board</h1>
        <p>What your constituency has raised — and what has been done. The record the MP sees is the record you see here.</p>
        <div className="pb-stats">
          <div className="stat-pill">
            <span className="dot pulse-blue"></span>
            <b>{board.open.length}</b> Issues being heard
          </div>
          <div className="stat-pill">
            <span className="dot ok"></span>
            <b>{board.resolved.length}</b> Resolved
          </div>
        </div>
      </div>

      <main className="pb-main">
        <section className="pb-section stagger-2">
          <h2 className="section-title">Currently Being Heard</h2>
          <div className="pb-list">
            {board.open.length === 0 && <div className="empty-state">Nothing on the record yet for this constituency.</div>}
            {board.open.map(i => (
              <div className="pb-card hover-lift" key={i.id}>
                <div className="pb-card-main">
                  <span className={`badge badge-${i.category}`}>{i.category}</span>
                  <h3>{i.title}</h3>
                  <div className="pb-meta">
                    <span className="icon">👥</span> Raised by {i.signal_count} {i.signal_count === 1 ? 'resident' : 'residents'}
                    {i.ward_name && <><span className="dot-sep">·</span><span className="icon">📍</span> {i.ward_name}</>}
                  </div>
                </div>
                <div className="pb-card-status">
                  {i.status === 'in_progress' ? (
                    <span className="badge badge-progress">Work in Progress</span>
                  ) : (
                    <span className="badge badge-open">Under Review</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="pb-section stagger-3">
          <h2 className="section-title">Resolved Works</h2>
          <div className="pb-list">
            {board.resolved.length === 0 && <div className="empty-state">Resolved works will appear here.</div>}
            {board.resolved.map(i => (
              <div className="pb-card pb-card-resolved" key={i.id}>
                <div className="pb-card-main">
                  <span className="badge badge-resolved">✓ Resolved</span>
                  <h3>{i.title}</h3>
                  <div className="pb-meta">
                    <span className="icon">👥</span> Raised by {i.signal_count} residents
                    {i.ward_name && <><span className="dot-sep">·</span><span className="icon">📍</span> {i.ward_name}</>}
                    {i.resolved_on && <><span className="dot-sep">·</span><span className="icon">🗓</span> Resolved {i.resolved_on}</>}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        <div className="pb-cta-banner stagger-4">
          <div className="cta-content">
            <h3>Raise an issue from your street</h3>
            <p>Send a WhatsApp message — voice, photo, or text, in your own language. You'll get a reference number, and your issue joins this public record.</p>
          </div>
          <a className="btn-primary" href="https://wa.me/14155238886" target="_blank" rel="noreferrer">Send via WhatsApp</a>
        </div>
      </main>
    </div>
  )
}
