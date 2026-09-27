import HubDrawing from '../components/HubDrawing'
import { SLOTS } from '../data'

function greeting() {
  const h = new Date().getHours()
  return h < 12 ? 'Good morning' : h < 18 ? 'Good afternoon' : 'Good evening'
}

export default function Dashboard({ nodes, profile, onSelectNode, onOpenProfile }) {
  const active = SLOTS.filter((s) => nodes[s.id].fn && nodes[s.id].availability !== 'off').length
  const treatLimit = nodes.N5.fn === 'food' ? nodes.N5.limit : null

  return (
    <div className="dashboard">
      <div className="hello">
        <div>
          <p className="muted">{greeting()}</p>
          <h1>{profile.name} is resting</h1>
          <div className="status">
            <span className="status-dot" /> Online · {active} of 5 nodes on
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
        <div className="stat"><strong>12</strong><span>Boops</span></div>
        <div className="stat"><strong>3</strong><span>Requests</span></div>
        <div className="stat">
          <strong>3{treatLimit && <small>/{treatLimit}</small>}</strong>
          <span>Treats</span>
        </div>
      </div>

      <div className="recent">
        <span className="muted">Latest</span>
        <p>{profile.name} asked to go out · 4:12 PM</p>
      </div>
    </div>
  )
}
