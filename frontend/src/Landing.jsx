import { useEffect, useState } from 'react'

export default function Landing() {
  const [stats, setStats] = useState({ voices: '—', wards: '—' })

  useEffect(() => {
    fetch('/api/demands?c=south-delhi').then(r => r.json()).then(d => {
      const demands = d.demands || []
      setStats({
        voices: demands.reduce((n, x) => n + (x.signal_count || 0), 0),
        wards: new Set(demands.map(x => x.ward_code).filter(Boolean)).size,
      })
    }).catch(() => {})
  }, [])

  return (
    <div className="landing">
      <header>
        <div className="wordmark">
          <span className="dev">सुनवाई</span>
          <span className="latin">sunwai</span>
        </div>
        <span className="spacer" />
        <nav className="landing-nav">
          <a href="/board">public board</a>
          <a href="https://github.com/noblenihal/sunwai" target="_blank" rel="noreferrer">github</a>
          <a className="btn-brief" href="/app">Open MP dashboard</a>
        </nav>
      </header>

      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow-line">
            <span className="live-dot" /> दर्ज THE RECORD · BUILD WITH AI: CODE FOR COMMUNITIES · TRACK 01
          </p>
          <h1>
            <span className="dev-big">हर आवाज़ दर्ज।</span><br />
            Every voice, on the record.
          </h1>
          <p className="lede">
            An MP represents 25 lakh people — and today, the loudest voice wins.
            sunwai turns WhatsApp voice notes, photos, and texts in any Indian
            language into evidence-ranked development priorities an MP's office
            can defend in public.
          </p>
          <div className="cta-row">
            <a className="btn-brief btn-lg" href="/app">Open the MP dashboard</a>
            <a className="btn-ghost" href="/board">See the public board ↗</a>
          </div>
          <p className="fact hero-stats">
            <b>{stats.voices}</b> voices on record · <b>{stats.wards}</b> wards heard ·
            5 constituencies · 7 languages · Gemini-powered
          </p>
        </div>

        <div className="hero-demo" aria-label="How a voice note becomes a record">
          <div className="chat">
            <div className="chat-title">WhatsApp · sunwai</div>
            <div className="bubble citizen">
              🎤 <i>voice note · 0:10</i><br />
              "गोविंदपुरी गली 4 में नाली दो हफ्ते से जाम है…"
            </div>
            <div className="bubble bot">
              ✅ <b>दर्ज हुआ</b> — नाली (drainage)<br />
              📌 संदर्भ: #S48 · 📍 Govind Puri<br />
              <span className="bubble-en">Recorded — drainage. Ref #S48.</span>
            </div>
          </div>
          <div className="flow-arrow">↓ Gemini structures it</div>
          <div className="record-card">
            <div className="record-card-head">
              <span className="pill">drainage</span>
              <strong>Blocked drain in Govindpuri Street 4</strong>
            </div>
            <div className="fact">55 submissions · ↑50%/wk · urgency 4/5</div>
            <div className="fact">Ward 176 · pop 74,651 (Census 2011) · ranked with evidence</div>
          </div>
        </div>
      </section>

      <section className="steps">
        <h2>Noise in. Evidence out.</h2>
        <div className="step-grid">
          <div className="step">
            <span className="step-no">01</span>
            <strong>Speak</strong>
            <p>Voice, photo, or text on WhatsApp — any Indian language, no app,
            no forms. The bot asks for what's missing, and answers work by voice.</p>
          </div>
          <div className="step">
            <span className="step-no">02</span>
            <strong>Structure</strong>
            <p>Gemini transcribes, categorizes, geolocates, and grades urgency.
            The same demand in Hindi, English, or Bangla merges into one record.</p>
          </div>
          <div className="step">
            <span className="step-no">03</span>
            <strong>Weigh</strong>
            <p>Every demand is cross-checked against Census and government ward
            data. Rank = submissions × trend × evidence gap — formula visible.</p>
          </div>
          <div className="step">
            <span className="step-no">04</span>
            <strong>Act</strong>
            <p>The office works a ranked list with written justifications; the
            public board shows what's raised, in progress, and resolved.</p>
          </div>
        </div>
      </section>

      <section className="features">
        <div className="feature">
          <strong>Silent Needs</strong>
          <p>AI that listens is good. AI that notices who <i>isn't</i> speaking
          is governance — high-need, low-voice wards get flagged for field visits.</p>
        </div>
        <div className="feature">
          <strong>Evidence, not vibes</strong>
          <p>Facts cite their sources: Census 2011, SEC Delimitation 2022.
          Individuals are never profiled — equity analysis is geographic.</p>
        </div>
        <div className="feature">
          <strong>One config file per constituency</strong>
          <p>Live today across South Delhi, Kolkata Dakshin, Ahmedabad East,
          Mumbai North East, and Chennai South — on one ₹1,000/month server.</p>
        </div>
      </section>

      <footer className="landing-footer">
        <span>सुनवाई sunwai — Build with AI: Code for Communities · Track 01 People's Priorities</span>
        <span className="spacer" />
        <a href="/app">dashboard</a>
        <a href="/board">public board</a>
        <a href="/api/brief">MP brief</a>
        <a href="https://github.com/noblenihal/sunwai" target="_blank" rel="noreferrer">source</a>
      </footer>
    </div>
  )
}
