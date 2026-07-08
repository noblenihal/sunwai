import { useEffect, useState } from 'react'

// Citizen-facing transparency board at /board — plain language, no login.
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
    <>
      <header>
        <div className="wordmark">
          <span className="dev">सुनवाई</span>
          <span className="latin">sunwai</span>
        </div>
        <span className="tagline">what your constituency has raised — and what has been done</span>
        <label className="file-label">
          <select value={con} onChange={e => setCon(e.target.value)} aria-label="Constituency">
            {constituencies.map(x => (
              <option key={x.code} value={x.code}>{x.name}, {x.state}</option>
            ))}
          </select>
        </label>
      </header>

      <div className="record-strip">
        <span className="eyebrow"><span className="dev">दर्ज</span> PUBLIC RECORD</span>
        <span><b>{board.open.length}</b> issues being heard</span>
        <span><b>{board.resolved.length}</b> resolved</span>
        <span>{conMeta ? `${conMeta.name}, ${conMeta.state}` : ''}</span>
      </div>

      <main>
        <section aria-labelledby="open-h">
          <h2 id="open-h" style={{ fontSize: 17, marginBottom: 10 }}>Being heard</h2>
          {board.open.length === 0 && <div className="card muted">Nothing on the record yet for this constituency.</div>}
          {board.open.map(i => (
            <div className="row" key={i.id}>
              <span className="pill">{i.category}</span>
              <strong>{i.title}</strong>
              {i.status === 'in_progress' && <span className="pill pill-visit" style={{ marginLeft: 8 }}>work in progress</span>}
              <div className="fact" style={{ marginTop: 4 }}>
                raised by {i.signal_count} {i.signal_count === 1 ? 'resident' : 'residents'}
                {i.ward_name ? ` · ${i.ward_name}` : ''}
              </div>
            </div>
          ))}
        </section>

        <section aria-labelledby="resolved-h" style={{ marginTop: 34 }}>
          <h2 id="resolved-h" style={{ fontSize: 17, marginBottom: 10 }}>Resolved</h2>
          {board.resolved.length === 0 && <div className="card muted">Resolved works will appear here.</div>}
          {board.resolved.map(i => (
            <div className="row" key={i.id} style={{ opacity: 0.85 }}>
              <span className="pill" style={{ background: '#e8f4ec', color: '#1e7a3c' }}>✓ resolved</span>
              <strong>{i.title}</strong>
              <div className="fact" style={{ marginTop: 4 }}>
                raised by {i.signal_count} {i.signal_count === 1 ? 'resident' : 'residents'}
                {i.ward_name ? ` · ${i.ward_name}` : ''}
                {i.resolved_on ? ` · resolved ${i.resolved_on}` : ''}
              </div>
            </div>
          ))}
        </section>

        <div className="card" style={{ marginTop: 34, background: 'var(--blue-tint)', border: '1px solid var(--rule)' }}>
          <strong>Raise an issue from your street</strong>
          <p className="muted" style={{ marginTop: 6 }}>
            Send a WhatsApp message — voice, photo or text, in your own language.
            You'll get a reference number, and your issue joins this public record.
          </p>
        </div>
      </main>
    </>
  )
}
