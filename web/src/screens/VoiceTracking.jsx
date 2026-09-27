import { useState } from 'react'
import {
  AudioLines, Cookie, Hand, Info, Megaphone, Mic, Music, Play, Smartphone, Volume2,
} from 'lucide-react'
import WeekBars from '../components/WeekBars'

// Mock data. Last value in each week is today.
const YOU_WEEK = [6, 9, 4, 11, 7, 8, 5]
const BARK_WEEK = [3, 5, 2, 6, 4, 3, 4]

const LOG = [
  { kind: 'bark', time: '4:10 PM', title: 'Bark activation', detail: '3 barks · Laika played calming music', Icon: AudioLines },
  { kind: 'you', time: '3:12 PM', title: 'You talked through Laika', detail: 'Voice message · 0:24', Icon: Megaphone },
  { kind: 'you', time: '2:40 PM', title: 'You sent a treat', detail: 'From the app · confirmed by sensor', Icon: Cookie },
  { kind: 'you', time: '1:05 PM', title: 'You started music', detail: 'From the app · 20 min', Icon: Music },
  { kind: 'bark', time: '11:32 AM', title: 'Bark activation', detail: '2 barks · no action (cooldown)', Icon: AudioLines },
  { kind: 'you', time: '10:18 AM', title: 'You confirmed a walk', detail: 'Harness released on the mat', Icon: Hand },
  { kind: 'bark', time: '9:47 AM', title: 'Bark activation', detail: '5 barks · you were notified', Icon: AudioLines },
  { kind: 'you', time: '8:02 AM', title: 'You answered a request', detail: 'Go out · responded in 3 min', Icon: Smartphone },
  { kind: 'bark', time: '7:15 AM', title: 'Bark activation', detail: '1 bark · Laika wiggled its ears', Icon: AudioLines },
]

const RESPONSES = [
  { id: 'music', label: 'Play calming music' },
  { id: 'notify', label: 'Just notify me' },
  { id: 'ears', label: 'Wiggle ears only' },
]

export default function VoiceTracking({ profile }) {
  const [filter, setFilter] = useState('all')
  const [barkOn, setBarkOn] = useState(true)
  const [response, setResponse] = useState('music')
  const [sensitivity, setSensitivity] = useState('medium')
  const name = profile.name
  const you = LOG.filter((e) => e.kind === 'you').length
  const barks = LOG.filter((e) => e.kind === 'bark').length
  const shown = filter === 'all' ? LOG : LOG.filter((e) => e.kind === filter)

  return (
    <div className="voice">
      <div className="voice-tiles">
        <div className="vtile vtile-you">
          <Hand size={18} />
          <strong>{you}</strong>
          <span>Your interactions with {name} today</span>
        </div>
        <div className="vtile vtile-bark">
          <AudioLines size={18} />
          <strong>{barks}</strong>
          <span>Times {name} activated Laika by barking</span>
        </div>
      </div>

      <section className="card">
        <div className="card-head">
          <h3 className="card-title"><Hand size={14} /> Your interactions · last 7 days</h3>
        </div>
        <WeekBars values={YOU_WEEK} tone="sage" unit="interactions" />
      </section>

      <section className="card">
        <div className="card-head">
          <h3 className="card-title"><AudioLines size={14} /> Bark activations · last 7 days</h3>
        </div>
        <WeekBars values={BARK_WEEK} tone="ochre" unit="bark activations" />
      </section>

      <section className="card">
        <div className="card-head">
          <h3 className="card-title">Today’s log</h3>
          <div className="seg-toggle">
            {[['all', 'All'], ['you', 'You'], ['bark', 'Barks']].map(([id, l]) => (
              <button key={id} className={filter === id ? 'is-on' : ''} onClick={() => setFilter(id)}>{l}</button>
            ))}
          </div>
        </div>
        <ul className="vlog">
          {shown.map((e) => (
            <li key={e.time} className={`vlog-${e.kind}`}>
              <span className="vlog-icon"><e.Icon size={16} /></span>
              <div className="vlog-main">
                <strong>{e.title}</strong>
                <span>{e.detail}</span>
              </div>
              <div className="vlog-side">
                <time>{e.time}</time>
                {e.kind === 'bark' && (
                  <button className="vlog-play" aria-label="Play recording"><Play size={11} fill="currentColor" /></button>
                )}
              </div>
            </li>
          ))}
        </ul>
      </section>

      <section className="card">
        <div className="card-head">
          <h3 className="card-title"><Mic size={14} /> Bark activation</h3>
          <input type="checkbox" className="switch" checked={barkOn} onChange={(e) => setBarkOn(e.target.checked)} aria-label="Bark activation" />
        </div>
        <p className="muted small section-hint">Let Laika respond when {name} barks near the hub.</p>
        {barkOn && (
          <>
            <div className="offer-list">
              {RESPONSES.map((r) => (
                <label key={r.id} className={`radio ${response === r.id ? 'is-on' : ''}`}>
                  <input type="radio" name="bark-response" checked={response === r.id} onChange={() => setResponse(r.id)} />
                  <span className="radio-mark" />
                  <span className="radio-label">{r.label}</span>
                </label>
              ))}
            </div>
            <div className="row">
              <span><Volume2 size={14} className="inline-icon" /> Sensitivity</span>
              <div className="seg-toggle">
                {['low', 'medium', 'high'].map((s) => (
                  <button key={s} className={sensitivity === s ? 'is-on' : ''} onClick={() => setSensitivity(s)}>
                    {s[0].toUpperCase() + s.slice(1)}
                  </button>
                ))}
              </div>
            </div>
          </>
        )}
        <p className="note"><Info size={14} /> Laika never gives treats for barking, so {name} doesn’t learn that barking earns rewards.</p>
      </section>
    </div>
  )
}
