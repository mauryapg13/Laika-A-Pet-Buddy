import { useEffect, useState } from 'react'
import {
  ArrowUpRight, BookOpen, Brain, Check, HeartPulse, Info, Lightbulb, Minus, Sparkles, Timer, X,
} from 'lucide-react'
import Icon from '../components/Icon'
import IdleBars from '../components/IdleBars'
import RhythmHeatmap from '../components/RhythmHeatmap'
import { entryFor } from '../diary'
import { BALANCE, PATTERNS, PREDICTIONS, RANGES, SUGGESTIONS } from '../insights'

const OFFERS = [
  { id: 'tug', label: 'Gentle tug', sub: 'N4 strap extends, low resistance' },
  { id: 'music', label: 'Calming music', sub: 'Boop pad glows to invite' },
  { id: 'scent', label: 'Scent game', sub: 'Hide-and-find with a token' },
]

function DaySummary({ date, name, onClear, onOpenDiary }) {
  const entry = entryFor(date)
  const label = date.toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' })
  const s = entry?.stats

  return (
    <section className="card day-card">
      <div className="card-head">
        <h3 className="card-title"><Sparkles size={14} /> Summary · {label}</h3>
        <button className="icon-btn icon-btn-sm" onClick={onClear} aria-label="Close day summary"><X size={16} /></button>
      </div>
      {entry ? (
        <>
          <p className="ai-text">
            {name} went on {s.walks} walks, took {s.naps} naps and had {s.treats} treats. The hub recorded {s.boops} boops
            and {s.barks} bark events. Highlights: {entry.clips.map((c) => `${c[1].toLowerCase()} (${c[0]})`).join(', ')}.
          </p>
          <button className="link-btn" onClick={onOpenDiary}><BookOpen size={14} /> Read {name}’s diary entry</button>
        </>
      ) : (
        <p className="muted small">No data for this day. The hub was offline.</p>
      )}
    </section>
  )
}

export default function Insights({ profile, date, onClearDate, onOpenDiary }) {
  const [range, setRange] = useState('week')
  const [autoPlay, setAutoPlay] = useState(true)
  const [idleAfter, setIdleAfter] = useState(120)
  const [offer, setOffer] = useState('tug')
  const [homeOnly, setHomeOnly] = useState(false)
  const [decided, setDecided] = useState({})
  const [idleNow, setIdleNow] = useState(85)
  const name = profile.name
  const r = RANGES[range]

  // Tick the live idle counter so the card feels alive.
  useEffect(() => {
    const t = setInterval(() => setIdleNow((m) => m + 1), 60000)
    return () => clearInterval(t)
  }, [])

  const remaining = Math.max(0, idleAfter - idleNow)
  const fmt = (m) => (m >= 60 ? `${Math.floor(m / 60)}h ${m % 60}m` : `${m} min`)

  return (
    <div className="insights">
      {date && <DaySummary date={date} name={name} onClear={onClearDate} onOpenDiary={onOpenDiary} />}

      <div className="insights-head">
        <h1>Insights</h1>
        <div className="seg-toggle">
          {Object.entries(RANGES).map(([id, v]) => (
            <button key={id} className={range === id ? 'is-on' : ''} onClick={() => setRange(id)}>{v.label}</button>
          ))}
        </div>
      </div>

      <section className="ai-card">
        <div className="ai-kicker"><Sparkles size={14} /> AI summary</div>
        <p className="ai-lead">{r.summary.replace('{name}', name)}</p>
        <p className="ai-source">Based on {r.events.toLocaleString()} recorded events · every claim links to a sensor or camera event</p>
      </section>

      <section className="card learn">
        <div className="learn-top">
          <div className="learn-icon"><Brain size={18} /></div>
          <div>
            <strong>Laika knows {name}’s routine well</strong>
            <span>Learning for 18 days · patterns 72% confident</span>
          </div>
        </div>
        <div className="learn-steps">
          {['Observing', 'Learning', 'Predicting', 'Personalised'].map((s, i) => (
            <div key={s} className={`learn-step ${i < 2 ? 'is-done' : i === 2 ? 'is-now' : ''}`}>
              <span />{s}
            </div>
          ))}
        </div>
      </section>

      <section className="card">
        <div className="card-head">
          <h3 className="card-title">{name}’s daily rhythm</h3>
        </div>
        <p className="muted small section-hint">What Laika has learned about when things usually happen. Tap a square.</p>
        <RhythmHeatmap />
      </section>

      <section className="card">
        <div className="card-head">
          <h3 className="card-title"><Timer size={14} /> Coming up today</h3>
        </div>
        <ul className="predictions">
          {PREDICTIONS.map((p) => (
            <li key={p.label}>
              <span className="pred-icon"><Icon name={p.icon} size={17} /></span>
              <div className="pred-main">
                <strong>{p.label}</strong>
                <span>Around {p.time} · usually {p.window}</span>
              </div>
              <div className="pred-conf" title="Confidence">
                <span>{Math.round(p.confidence * 100)}%</span>
                <i><b style={{ width: `${p.confidence * 100}%` }} /></i>
              </div>
            </li>
          ))}
        </ul>
      </section>

      <section className="card boredom">
        <div className="card-head">
          <h3 className="card-title"><Lightbulb size={14} /> Boredom buster</h3>
          <input type="checkbox" className="switch" checked={autoPlay} onChange={(e) => setAutoPlay(e.target.checked)} aria-label="Boredom buster" />
        </div>
        <p className="muted small section-hint">
          When {name} has been awake and idle for a while, Laika offers something to do. {name} chooses whether to join,
          and if not, the offer quietly ends.
        </p>

        {autoPlay && (
          <>
            <div className="live">
              <div className="live-top">
                <span className="live-dot" /> <strong>Idle for {fmt(idleNow)}</strong>
                <span className="muted">{remaining ? `offer in ${fmt(remaining)}` : 'offering now'}</span>
              </div>
              <i className="live-bar"><b style={{ width: `${Math.min(100, (idleNow / idleAfter) * 100)}%` }} /></i>
            </div>

            <div className="row">
              <span>Offer after idle for</span>
              <div className="seg-toggle">
                {[60, 120, 180].map((m) => (
                  <button key={m} className={idleAfter === m ? 'is-on' : ''} onClick={() => setIdleAfter(m)}>{m / 60}h</button>
                ))}
              </div>
            </div>

            <div className="offer-list">
              {OFFERS.map((o) => (
                <label key={o.id} className={`radio ${offer === o.id ? 'is-on' : ''}`}>
                  <input type="radio" name="offer" checked={offer === o.id} onChange={() => setOffer(o.id)} />
                  <span className="radio-mark" />
                  <span>
                    <span className="radio-label">{o.label}</span>
                    <span className="radio-sub">{o.sub}</span>
                  </span>
                </label>
              ))}
            </div>

            <label className="row">
              <span>Only when someone’s home</span>
              <input type="checkbox" className="switch" checked={homeOnly} onChange={(e) => setHomeOnly(e.target.checked)} />
            </label>

            <div className="offer-log">
              <span className="muted">Yesterday 2:14 PM</span>
              <p>Offered tug after 2h 10m idle · {name} joined for 48 sec</p>
            </div>
          </>
        )}
      </section>

      <section className="card">
        <div className="card-head">
          <h3 className="card-title"><HeartPulse size={14} /> Wellbeing signals</h3>
        </div>
        <div className="balance">
          {BALANCE.map((b) => (
            <div key={b.label} className="bal">
              <span>{b.label}</span>
              <strong>{b.value}</strong>
              <em>
                {b.trend === 'up' ? <ArrowUpRight size={12} /> : <Minus size={12} />} {b.delta}
              </em>
            </div>
          ))}
        </div>
        <IdleBars />
        <div className="signal">
          <strong>Possible under-stimulation on Mon & Tue</strong>
          <p>Idle stretches were 40–50% longer than usual and play requests dropped. More enrichment in the early afternoon might help.</p>
        </div>
        <p className="note"><Info size={14} /> These are patterns Laika has noticed, not a diagnosis. If something seems off, check with your vet.</p>
      </section>

      <section className="card">
        <div className="card-head">
          <h3 className="card-title">Patterns Laika noticed</h3>
        </div>
        <ul className="patterns">
          {PATTERNS.map((p) => (
            <li key={p.title}><strong>{p.title}</strong><span>{p.detail}</span></li>
          ))}
        </ul>
      </section>

      <section className="card">
        <div className="card-head">
          <h3 className="card-title">Suggestions for you</h3>
        </div>
        <p className="muted small section-hint">Laika never changes settings without your OK.</p>
        {SUGGESTIONS.map((s) => (
          <div key={s.id} className="suggest">
            <strong>{s.title}</strong>
            <p>{s.detail}</p>
            {decided[s.id] ? (
              <span className={`pill ${decided[s.id] === 'yes' ? '' : 'pill-muted'}`}>
                {decided[s.id] === 'yes' ? <><Check size={12} /> Applied</> : 'Dismissed'}
              </span>
            ) : (
              <div className="suggest-actions">
                <button className="btn-chip" onClick={() => setDecided({ ...decided, [s.id]: 'no' })}>Not now</button>
                <button className="btn-chip btn-chip-primary" onClick={() => setDecided({ ...decided, [s.id]: 'yes' })}>Apply</button>
              </div>
            )}
          </div>
        ))}
      </section>
    </div>
  )
}
