import { useState } from 'react'
import {
  BellRing, ChevronRight, Cpu, Globe, LogOut, OctagonX, Plus, RefreshCw, Shield, ShieldAlert, Trash2, UserRound, Video, Wifi,
} from 'lucide-react'
import Sheet from '../components/Sheet'

const PEOPLE = [
  { name: 'You', role: 'Owner', initial: 'Y' },
  { name: 'Jordan', role: 'Dog walker · weekdays', initial: 'J' },
]

function Group({ title, Icon, children }) {
  return (
    <section className="card settings-group">
      <h3 className="card-title">{Icon && <Icon size={14} />} {title}</h3>
      {children}
    </section>
  )
}

function Toggle({ label, sub, checked, onChange }) {
  return (
    <label className="row">
      <span>{label}{sub && <span className="row-sub">{sub}</span>}</span>
      <input type="checkbox" className="switch" checked={checked} onChange={(e) => onChange(e.target.checked)} />
    </label>
  )
}

function LinkRow({ label, value, onClick, danger }) {
  return (
    <button className={`row link-row ${danger ? 'danger' : ''}`} onClick={onClick}>
      <span>{label}</span>
      <span className="link-row-end">{value && <span className="muted">{value}</span>}<ChevronRight size={16} className="muted" /></span>
    </button>
  )
}

export default function Settings({ profile, onHelp }) {
  const [s, setS] = useState({
    requests: true, sessions: true, unusual: true, barks: false, diary: true, quiet: true,
    camera: true, mic: true, cloud: false, retention: 30,
    dispensing: true, resistance: true, units: 'kg',
  })
  const [stopOpen, setStopOpen] = useState(false)
  const [stopped, setStopped] = useState(false)
  const [toast, setToast] = useState(null)
  const set = (k) => (v) => setS((p) => ({ ...p, [k]: v }))
  const say = (msg) => { setToast(msg); setTimeout(() => setToast(null), 2000) }
  const name = profile.name

  return (
    <div className="settings">
      {stopped && (
        <div className="stop-banner">
          <OctagonX size={18} />
          <span>All motors stopped. Straps are loose and dispensing is off.</span>
          <button onClick={() => setStopped(false)}>Resume</button>
        </div>
      )}

      <section className="account">
        <div className="account-avatar"><UserRound size={24} /></div>
        <div>
          <strong>Your account</strong>
          <span>you@example.com</span>
        </div>
        <button className="btn-chip" onClick={() => say('Account editing is coming soon')}>Edit</button>
      </section>

      <Group title="Household" Icon={UserRound}>
        {PEOPLE.map((p) => (
          <div key={p.name} className="row person">
            <span className="person-avatar">{p.initial}</span>
            <span className="person-main"><strong>{p.name}</strong><span className="row-sub">{p.role}</span></span>
          </div>
        ))}
        <button className="link-btn add-person" onClick={() => say('Invite link copied')}><Plus size={14} /> Invite someone</button>
      </Group>

      <Group title="Laika hub" Icon={Cpu}>
        <div className="hub-status">
          <div><span className="status-dot" /> Online</div>
          <div><Wifi size={14} /> Strong</div>
          <div>Firmware 0.1.4</div>
        </div>
        <LinkRow label="Hub name" value="Study" onClick={() => say('Rename coming soon')} />
        <LinkRow label="Check for updates" value="Up to date" onClick={() => say('Laika is up to date')} />
        <LinkRow label="Test wall mount" onClick={() => say('Mount check passed')} />
        <button className="row link-row" onClick={() => say('Restarting hub…')}>
          <span><RefreshCw size={14} className="inline-icon" /> Restart hub</span>
        </button>
      </Group>

      <Group title="Safety" Icon={Shield}>
        <button className="estop" onClick={() => setStopOpen(true)} disabled={stopped}>
          <OctagonX size={20} /> {stopped ? 'Motors stopped' : 'Emergency stop'}
        </button>
        <Toggle label="Treat dispensing" sub="Turn off to block all food output" checked={s.dispensing} onChange={set('dispensing')} />
        <Toggle label="Tug and resistance play" sub="Off parks every pull strap" checked={s.resistance} onChange={set('resistance')} />
      </Group>

      <Group title="Notifications" Icon={BellRing}>
        <Toggle label="Requests" sub={`When ${name} asks to go out or for attention`} checked={s.requests} onChange={set('requests')} />
        <Toggle label="Session summaries" sub="After tug or play sessions end" checked={s.sessions} onChange={set('sessions')} />
        <Toggle label="Unusual activity" sub="Repeated pulls, long idle stretches" checked={s.unusual} onChange={set('unusual')} />
        <Toggle label="Bark alerts" checked={s.barks} onChange={set('barks')} />
        <Toggle label="Diary is ready" sub="Every evening at 8:00 PM" checked={s.diary} onChange={set('diary')} />
        <Toggle label="Quiet hours" sub="10:00 PM – 7:00 AM, urgent alerts only" checked={s.quiet} onChange={set('quiet')} />
      </Group>

      <Group title="Privacy & cameras" Icon={Video}>
        <Toggle label="Cameras" checked={s.camera} onChange={set('camera')} />
        <Toggle label="Microphone" sub="Needed for bark detection" checked={s.mic} onChange={set('mic')} />
        <Toggle label="Save clips to the cloud" sub="Off: video stays on the hub" checked={s.cloud} onChange={set('cloud')} />
        <div className="row">
          <span>Keep recordings for</span>
          <select value={s.retention} onChange={(e) => set('retention')(Number(e.target.value))}>
            {[7, 30, 90].map((d) => <option key={d} value={d}>{d} days</option>)}
          </select>
        </div>
        <button className="row link-row danger" onClick={() => say('History deleted')}>
          <span><Trash2 size={14} className="inline-icon" /> Delete all recordings & history</span>
        </button>
      </Group>

      <Group title="Preferences" Icon={Globe}>
        <div className="row">
          <span>Weight units</span>
          <div className="seg-toggle">
            {['kg', 'lb'].map((u) => (
              <button key={u} className={s.units === u ? 'is-on' : ''} onClick={() => set('units')(u)}>{u}</button>
            ))}
          </div>
        </div>
        <LinkRow label="Language" value="English" onClick={() => say('More languages coming soon')} />
      </Group>

      <Group title="Support" Icon={ShieldAlert}>
        <LinkRow label="Help & training guides" onClick={onHelp} />
        <LinkRow label="Terms & privacy policy" onClick={() => say('Opens in browser')} />
        <button className="row link-row danger" onClick={() => say('Signed out (not really, it’s a mockup)')}>
          <span><LogOut size={14} className="inline-icon" /> Sign out</span>
        </button>
      </Group>

      <p className="settings-foot">Laika · app 0.1.0</p>

      {toast && <div className="toast toast-fixed">{toast}</div>}

      {stopOpen && (
        <Sheet
          title="Stop all motors?"
          kicker="Emergency stop"
          onClose={() => setStopOpen(false)}
          footer={
            <>
              <button className="btn btn-ghost" onClick={() => setStopOpen(false)}>Cancel</button>
              <button className="btn btn-danger" onClick={() => { setStopped(true); setStopOpen(false) }}>Stop now</button>
            </>
          }
        >
          <p className="stop-copy">
            Every strap goes loose, retraction stops, and dispensing turns off right away. Nothing will move until you resume.
          </p>
        </Sheet>
      )}
    </div>
  )
}
