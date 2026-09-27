import HubDrawing from '../components/HubDrawing'
import { SLOTS } from '../data'
import { BEHAVIOUR_TEXT, parseNotification } from '../api'

function greeting() {
  const h = new Date().getHours()
  return h < 12 ? 'Good morning' : h < 18 ? 'Good afternoon' : 'Good evening'
}

export default function Dashboard({ laika, nodes, profile, onSelectNode, onOpenProfile }) {
  const active = SLOTS.filter((s) => nodes[s.id].fn && nodes[s.id].availability !== 'off').length
  const treatLimit = nodes.N5.fn === 'food' ? nodes.N5.limit : null
  // Live numbers from the hub + camera when the back end is running; otherwise the mock values.
  const live = laika?.connected ? laika.live : null
  const hub = live?.hub
  const doing = live?.label ? BEHAVIOUR_TEXT[live.label] ?? live.label.replaceAll('_', ' ') : 'resting'
  const latest = hub?.notifications.length ? parseNotification(hub.notifications.at(-1), profile.name) : null
  const status = !live ? `Online · ${active} of 5 nodes on`
    : hub.device_state !== 'ONLINE' ? 'Emergency stop is on'
    : `Online · live${hub.mode !== 'idle' ? ` · ${hub.mode} on` : ''}${live.human ? ' · someone is home' : ''}`

  return (
    <div className="dashboard">
      <div className="hello">
        <div>
          <p className="muted">{greeting()}</p>
          <h1>{profile.name} is {live ? doing : 'resting'}</h1>
          <div className="status">
            <span className="status-dot" /> {status}
          </div>
        </div>
        <button className="avatar" onClick={onOpenProfile} aria-label={`${profile.name}'s profile`}>
          <img src={profile.photo} alt="" />
        </button>
      </div>

      <div className="hub-card">
        <HubDrawing nodes={nodes} onSelect={onSelectNode} />
        <p className="hint">Tap a node or the boop pad to set what it does</p>
      </div>

      <div className="stats">
        <div className="stat"><strong>{hub ? hub.counts.boops : 12}</strong><span>Boops</span></div>
        <div className="stat"><strong>{hub ? hub.counts.requests : 3}</strong><span>Requests</span></div>
        <div className="stat">
          <strong>{hub ? hub.treats : 3}{hub ? <small>/{hub.treats_limit}</small> : treatLimit && <small>/{treatLimit}</small>}</strong>
          <span>Treats</span>
        </div>
      </div>

      <div className="recent">
        <span className="muted">Latest</span>
        <p>{live ? (latest ? `${latest.text} · ${latest.time}` : 'Nothing yet today') : `${profile.name} asked to go out · 4:12 PM`}</p>
      </div>
    </div>
  )
}
