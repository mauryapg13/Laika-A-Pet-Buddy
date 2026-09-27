import { useState } from 'react'
import {
  BookOpen, Calendar, Check, ChevronDown, GraduationCap, Mail, MessageCircle, Phone, Rocket,
  Search, Shield, Unplug, Video, Wrench, X,
} from 'lucide-react'

const TOPICS = [
  { id: 'start', label: 'Getting started', Icon: Rocket },
  { id: 'training', label: 'Training', Icon: GraduationCap },
  { id: 'nodes', label: 'Nodes', Icon: Unplug },
  { id: 'safety', label: 'Safety', Icon: Shield },
  { id: 'privacy', label: 'Camera & privacy', Icon: Video },
  { id: 'fix', label: 'Troubleshooting', Icon: Wrench },
]

// PRD §9.7: training sequence for a new pull attachment.
const TRAINING = [
  ['Association', 'Show the available handle and reward calm sniffing.'],
  ['Simple action', 'A light pull gets an instant chime and ear lift.'],
  ['Release', 'Teach “drop it”. Laika waits for release before retracting.'],
  ['Short sessions', 'Add a few low-resistance pulls, then stop.'],
  ['Closing cue', 'Same sound, ear gesture and retraction every time.'],
  ['Unavailable', 'Only now introduce the parked state.'],
  ['Personalise', 'Let Laika fine-tune thresholds from good sessions.'],
]

// What the hub's ears and lights mean (PRD §6.3).
const CUES = [
  ['Ears slightly open', 'An activity is available'],
  ['One ear lifts', 'Action was successful'],
  ['Slow ear wave', 'Someone familiar arrived'],
  ['Ears lower slowly', 'Session is closing'],
  ['Handle tucked away', 'That activity is off right now'],
  ['Steady amber light', 'Something needs your attention in the app'],
]

const FAQS = [
  { topic: 'start', q: 'How do I set up a node?', a: 'On Home, tap any node on the hub drawing. Choose what it does, when it’s available and its limits, then tap Save changes.' },
  { topic: 'start', q: 'Can more than one person use the app?', a: 'Yes. Go to Settings → Household → Invite someone. Walkers and sitters can get limited access.' },
  { topic: 'training', q: 'How long does training take?', a: 'Most dogs learn one attachment in 1–2 weeks with short daily sessions. Move to the next step only when the current one feels easy.' },
  { topic: 'training', q: 'My dog pulls harder when a feature is off. What do I do?', a: 'That’s normal early on. Laika never rewards harder pulling: off means the handle is parked. Keep the closing cue consistent and the behaviour fades.' },
  { topic: 'nodes', q: 'Why is an option greyed out for a node?', a: 'Each node has different hardware. Food and walk need the output node (N5), and tug needs a pull node (N1 or N4).' },
  { topic: 'nodes', q: 'How do I add a new attachment?', a: 'Click it into any free node. Laika detects it automatically, then asks you what it should mean. It never guesses.' },
  { topic: 'safety', q: 'What does the emergency stop do?', a: 'Every strap goes loose, retraction stops and dispensing turns off right away. Find it in Settings → Safety.' },
  { topic: 'safety', q: 'Is tug play safe for small dogs?', a: 'Resistance is capped by dog size and ends if your dog lets go. Skip tug for dogs with neck, jaw or joint issues, and ask your vet if unsure.' },
  { topic: 'privacy', q: 'Where is my video stored?', a: 'On the hub by default. Cloud saving is off unless you turn it on in Settings → Privacy & cameras.' },
  { topic: 'privacy', q: 'How do I know when someone is watching live?', a: 'The hub shows a soft light whenever the live view is open.' },
  { topic: 'fix', q: 'A treat was requested but didn’t drop', a: 'Open the dispenser lid and check for a jam. Laika doesn’t retry automatically, so tap Test node on N5 after clearing it.' },
  { topic: 'fix', q: 'The strap won’t retract', a: 'Laika waits until the strap is released. If nothing is holding it, restart the hub from Settings → Laika hub.' },
  { topic: 'fix', q: 'The hub shows as offline', a: 'Check that the power light is on and your Wi-Fi is working. Your settings and limits keep running on the hub while it’s offline.' },
]

export default function Help({ profile }) {
  const [query, setQuery] = useState('')
  const [topic, setTopic] = useState(null)
  const [open, setOpen] = useState(null)
  const [done, setDone] = useState(3)
  const [contact, setContact] = useState(null)
  const name = profile.name

  const q = query.trim().toLowerCase()
  const faqs = FAQS.filter((f) =>
    (!topic || f.topic === topic) && (!q || (f.q + f.a).toLowerCase().includes(q)))
  const filtering = topic || q

  return (
    <div className="help">
      <div className="help-hero">
        <h1>How can we help?</h1>
        <label className="search">
          <Search size={17} />
          <input
            placeholder="Search guides and questions"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          {query && <button onClick={() => setQuery('')} aria-label="Clear"><X size={15} /></button>}
        </label>
      </div>

      <div className="topics">
        {TOPICS.map(({ id, label, Icon }) => (
          <button key={id} className={`topic ${topic === id ? 'is-on' : ''}`} onClick={() => setTopic(topic === id ? null : id)}>
            <Icon size={19} />
            <span>{label}</span>
          </button>
        ))}
      </div>

      {!filtering && (
        <>
          <section className="card">
            <div className="card-head">
              <h3 className="card-title"><GraduationCap size={14} /> {name}’s training plan</h3>
              <span className="muted small">{done} of {TRAINING.length}</span>
            </div>
            <i className="live-bar train-bar"><b style={{ width: `${(done / TRAINING.length) * 100}%` }} /></i>
            <ol className="steps">
              {TRAINING.map(([t, d], i) => (
                <li key={t} className={i < done ? 'is-done' : i === done ? 'is-now' : ''}>
                  <button className="step-mark" onClick={() => setDone(i < done ? i : i + 1)} aria-label={`Mark ${t}`}>
                    {i < done ? <Check size={13} /> : i + 1}
                  </button>
                  <div>
                    <strong>{t}</strong>
                    <span>{d}</span>
                  </div>
                </li>
              ))}
            </ol>
            <p className="note">Tap a number to mark a step done. Move on only when {name} finds the current step easy.</p>
          </section>

          <section className="card">
            <div className="card-head">
              <h3 className="card-title"><BookOpen size={14} /> What Laika is telling you</h3>
            </div>
            <ul className="cue-list">
              {CUES.map(([sign, meaning]) => (
                <li key={sign}><strong>{sign}</strong><span>{meaning}</span></li>
              ))}
            </ul>
          </section>
        </>
      )}

      <section className="card">
        <div className="card-head">
          <h3 className="card-title">
            {topic ? TOPICS.find((t) => t.id === topic).label : q ? 'Results' : 'Common questions'}
          </h3>
          {filtering && (
            <button className="link-btn" onClick={() => { setTopic(null); setQuery('') }}>Clear</button>
          )}
        </div>
        {faqs.length ? (
          <ul className="faqs">
            {faqs.map((f) => (
              <li key={f.q} className={open === f.q ? 'is-open' : ''}>
                <button onClick={() => setOpen(open === f.q ? null : f.q)}>
                  <span>{f.q}</span>
                  <ChevronDown size={16} />
                </button>
                {open === f.q && <p>{f.a}</p>}
              </li>
            ))}
          </ul>
        ) : (
          <p className="muted small">No matches. Try another word or contact us below.</p>
        )}
      </section>

      <section className="card">
        <div className="card-head">
          <h3 className="card-title">Still stuck?</h3>
        </div>
        <div className="contact-grid">
          <button className="contact" onClick={() => setContact('chat')}><MessageCircle size={20} /><span>Chat</span><em>~2 min reply</em></button>
          <button className="contact" onClick={() => setContact('email')}><Mail size={20} /><span>Email</span><em>Within a day</em></button>
          <button className="contact" onClick={() => setContact('call')}><Phone size={20} /><span>Call</span><em>9 AM – 6 PM</em></button>
        </div>
        <button className="trainer" onClick={() => setContact('trainer')}>
          <span className="trainer-icon"><Calendar size={18} /></span>
          <span className="trainer-main">
            <strong>Book a session with a trainer</strong>
            <span>30-minute video call about {name}’s training</span>
          </span>
        </button>
        {contact && (
          <p className="contact-confirm">
            <Check size={14} />
            {contact === 'chat' && 'A support person will join the chat shortly.'}
            {contact === 'email' && 'Email draft opened to support@laika.example.'}
            {contact === 'call' && 'Calling Laika support…'}
            {contact === 'trainer' && 'We’ll suggest times that work for you.'}
          </p>
        )}
      </section>
    </div>
  )
}
