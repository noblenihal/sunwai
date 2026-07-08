import { useEffect, useState } from 'react'

export default function Landing() {
  const [stats, setStats] = useState({ voices: '—', wards: '—' })

  useEffect(() => {
    fetch('/api/demands?c=south-delhi')
      .then(r => r.json())
      .then(d => {
        const demands = d.demands || []
        setStats({
          voices: demands.reduce((n, x) => n + (x.signal_count || 0), 0),
          wards: new Set(demands.map(x => x.ward_code).filter(Boolean)).size,
        })
      })
      .catch(() => {})
  }, [])

  return (
    <div className="landing-page">
      <header className="glass-header">
        <div className="wordmark">
          <img src="/logo.png" alt="Sunwai Logo" className="app-logo" />
          <span className="latin">Sunwai</span>
        </div>
        <span className="spacer" />
        <nav className="landing-nav">
          <a href="#how-to-use" className="nav-link">How to use</a>
          <a href="/board" className="nav-link">Public Board</a>
          <a href="https://github.com/noblenihal/sunwai" target="_blank" rel="noreferrer" className="nav-link">GitHub</a>
          <a className="btn-primary" href="/app">Open MP Dashboard</a>
        </nav>
      </header>

      <main className="landing-main">
        {/* Hero Section */}
        <section className="hero-section">
          <div className="hero-content stagger-1">
            <div className="eyebrow-badge">
              <span className="live-dot" /> ON THE RECORD · BUILD WITH AI
            </div>
            <h1 className="hero-title">
              Every voice, on the record.
            </h1>
            <p className="hero-subtitle">
              An MP represents 25 lakh people — and today, the loudest voice wins.
              Sunwai turns WhatsApp voice notes and photos into evidence-ranked development priorities that an MP can defend publicly.
            </p>
            <div className="cta-group">
              <a className="btn-primary btn-lg" href="/app">Open the Dashboard</a>
              <a className="btn-secondary btn-lg" href="/board">See the Public Board ↗</a>
            </div>
            <div className="hero-stats-row">
              <div className="stat-item">
                <span className="stat-val">{stats.voices}</span>
                <span className="stat-lbl">Voices Heard</span>
              </div>
              <div className="stat-item">
                <span className="stat-val">{stats.wards}</span>
                <span className="stat-lbl">Wards Mapped</span>
              </div>
              <div className="stat-item">
                <span className="stat-val">7</span>
                <span className="stat-lbl">Languages</span>
              </div>
              <div className="stat-item">
                <span className="stat-val">AI</span>
                <span className="stat-lbl">Gemini Powered</span>
              </div>
            </div>
          </div>

          <div className="hero-visual stagger-2">
            <div className="chat-simulation">
              <div className="chat-header">WhatsApp · Sunwai</div>
              <div className="chat-body">
                <div className="bubble citizen float-up">
                  🎤 <i>voice note · 0:10</i><br />
                  "The drain in Govindpuri Street 4 has been blocked for two weeks…"
                </div>
                <div className="bubble bot delay-1">
                  ✅ <b>Recorded</b> — drainage<br />
                  📌 Ref: #S48 · 📍 Govind Puri<br />
                </div>
              </div>
            </div>
            <div className="conversion-arrow">↓ Structured by Gemini ↓</div>
            <div className="insight-card delay-2">
              <div className="insight-head">
                <span className="badge badge-drainage">Drainage</span>
                <strong>Blocked drain in Govindpuri Street 4</strong>
              </div>
              <div className="insight-metrics">
                <span>🔥 ↑50% trend</span>
                <span>🚨 Urgency 4/5</span>
              </div>
              <div className="insight-foot">Ward 176 · Pop 74,651 · Ranked with evidence</div>
            </div>
          </div>
        </section>

        {/* Bento Box Features */}
        <section className="bento-section stagger-3">
          <h2 className="section-title">Noise in. Evidence out.</h2>
          <div className="bento-grid">
            <div className="bento-card span-2 bento-speak">
              <div className="step-no">01</div>
              <h3>Speak</h3>
              <p>Voice, photo, or text on WhatsApp — any Indian language, no app, no forms. The bot asks for what's missing, and answers work by voice.</p>
            </div>
            <div className="bento-card bento-structure">
              <div className="step-no">02</div>
              <h3>Structure</h3>
              <p>Gemini transcribes, categorizes, geolocates, and grades urgency. The same demand in Hindi, English, or Bangla merges into one record.</p>
            </div>
            <div className="bento-card bento-weigh">
              <div className="step-no">03</div>
              <h3>Weigh</h3>
              <p>Every demand is cross-checked against Census and government ward data. Rank = submissions × trend × evidence gap.</p>
            </div>
            <div className="bento-card span-2 bento-act">
              <div className="step-no">04</div>
              <h3>Act</h3>
              <p>The office works a ranked list with written justifications; the public board shows what's raised, in progress, and resolved.</p>
            </div>
          </div>
        </section>

        {/* How to use */}
        <section className="howto-section" id="how-to-use">
          <h2 className="section-title">How to use Sunwai</h2>
          <div className="howto-grid">
            <div className="howto-card howto-public">
              <div className="howto-head">
                <span className="howto-icon">🙋</span>
                <div>
                  <h3>I'm a resident</h3>
                  <p className="howto-sub">Report an issue from your street — 30 seconds, no app.</p>
                </div>
              </div>
              <ol className="howto-steps">
                <li><b>Message the Sunwai WhatsApp number.</b> Voice note, photo, or text — in your own language.</li>
                <li><b>Say what and where.</b> "The drain in Govindpuri Street 4 is blocked." If you forget the place, the bot asks — you can answer by voice.</li>
                <li><b>Get your reference number.</b> Instant reply: ✅ Recorded — Ref #S48.</li>
                <li><b>Track it publicly.</b> Your issue joins the <a href="/board">Public Board</a> — see it move from <i>being heard</i> to <i>resolved</i>.</li>
              </ol>
            </div>
            <div className="howto-card howto-office">
              <div className="howto-head">
                <span className="howto-icon">🏛️</span>
                <div>
                  <h3>I'm the MP's office</h3>
                  <p className="howto-sub">Work a ranked, evidence-backed list — not a mailbag.</p>
                </div>
              </div>
              <ol className="howto-steps">
                <li><b>Open the <a href="/app">dashboard</a>.</b> The Hotspot Map shows where demand burns, live, ward by ward.</li>
                <li><b>Read Ranked Works.</b> Every work carries its formula, Census-cited facts, and a written justification you can defend publicly.</li>
                <li><b>Tune the ranking.</b> Set weights, boost categories, or type priorities in plain language — the AI applies them transparently.</li>
                <li><b>Check Silent Needs.</b> High-need wards that aren't complaining get flagged for field visits.</li>
                <li><b>Act and close the loop.</b> Mark works in progress or resolved — the Public Board updates for everyone. Export the one-page MP Brief for the planning meeting.</li>
              </ol>
            </div>
          </div>
        </section>

        {/* Highlights Section */}
        <section className="highlights-section stagger-4">
          <div className="highlight-card">
            <div className="icon-wrapper">🤫</div>
            <h3>Silent Needs</h3>
            <p>AI that listens is good. AI that notices who <i>isn't</i> speaking is governance — high-need, low-voice wards get flagged for proactive field visits.</p>
          </div>
          <div className="highlight-card">
            <div className="icon-wrapper">📊</div>
            <h3>Evidence, not vibes</h3>
            <p>Facts cite their sources: Census 2011, SEC Delimitation 2022. Individuals are never profiled — equity analysis is strictly geographic.</p>
          </div>
          <div className="highlight-card">
            <div className="icon-wrapper">⚡</div>
            <h3>Instant Deploy</h3>
            <p>Live today across 5 major constituencies on a single ₹1,000/month server. Onboarding a new MP takes one config file.</p>
          </div>
        </section>
      </main>

      <footer className="glass-footer">
        <div className="footer-content">
          <span>Sunwai — Build with AI: Code for Communities · Track 01</span>
          <div className="footer-links">
            <a href="/app">Dashboard</a>
            <a href="/board">Public Board</a>
            <a href="/api/brief">MP Brief</a>
            <a href="https://github.com/noblenihal/sunwai" target="_blank" rel="noreferrer">Source</a>
          </div>
        </div>
      </footer>
    </div>
  )
}
