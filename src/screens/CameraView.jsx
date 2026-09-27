import { useEffect, useState } from 'react'
import {
  Camera as CameraIcon, CircleDot, Eye, EyeOff, Maximize2, Mic, Play, Volume2, VolumeX, WifiOff,
} from 'lucide-react'
import { entryFor } from '../diary'

// Mock cameras around the home. `look` applies a CSS treatment to the frame.
const CAMERAS = [
  { id: 'hub', name: 'Laika hub', room: 'Study', src: '/photos/dog-6169.jpg', pos: 'center 45%', dog: true },
  { id: 'study', name: 'Desk corner', room: 'Study', src: '/photos/dog-6170.jpg', pos: 'center 60%', dog: true, look: 'wide' },
  { id: 'hall', name: 'Hallway', room: 'Entrance', src: '/photos/cam-hallway.jpg', pos: 'center', motion: '12 min ago' },
  { id: 'bed', name: 'Bedroom', room: 'Upstairs', src: '/photos/dog-6168.jpg', pos: 'center 40%', look: 'night', motion: '1 hr ago' },
  { id: 'yard', name: 'Backyard', room: 'Outside', offline: true },
]

function Feed({ cam, big, now, muted }) {
  if (cam.offline) {
    return (
      <div className={`feed feed-offline ${big ? 'feed-big' : ''}`}>
        <WifiOff size={big ? 26 : 18} />
        <span>Offline</span>
      </div>
    )
  }
  return (
    <div className={`feed ${big ? 'feed-big' : ''} look-${cam.look || 'normal'}`}>
      <img src={cam.src} alt={`${cam.name} camera`} style={{ objectPosition: cam.pos }} />
      <span className="feed-live"><i /> LIVE</span>
      {big && (
        <span className="feed-time">
          {now.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', second: '2-digit' })}
        </span>
      )}
      {cam.look === 'night' && <span className="feed-ir">IR</span>}
      {big && muted && <span className="feed-muted"><VolumeX size={13} /></span>}
    </div>
  )
}

export default function CameraView({ profile, date }) {
  const [active, setActive] = useState('hub')
  const [mode, setMode] = useState(date ? 'recordings' : 'live')
  const [now, setNow] = useState(new Date())
  const [muted, setMuted] = useState(true)
  const [talking, setTalking] = useState(false)
  const [recording, setRecording] = useState(false)
  const [paused, setPaused] = useState(false)
  const [flash, setFlash] = useState(false)
  const cam = CAMERAS.find((c) => c.id === active)
  const name = profile.name
  const dogCam = CAMERAS.find((c) => c.dog)
  const recDate = date || new Date()
  const entry = entryFor(recDate)

  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(t)
  }, [])

  const snap = () => { setFlash(true); setTimeout(() => setFlash(false), 250) }

  return (
    <div className="cams">
      <div className="cam-locator">
        <span className="live-dot" />
        <span><strong>{name}</strong> is in the {dogCam.room.toLowerCase()}</span>
        <button className="link-btn" onClick={() => { setActive(dogCam.id); setMode('live') }}>Show me</button>
      </div>

      <div className="seg-toggle seg-full">
        <button className={mode === 'live' ? 'is-on' : ''} onClick={() => setMode('live')}>Live</button>
        <button className={mode === 'recordings' ? 'is-on' : ''} onClick={() => setMode('recordings')}>Recordings</button>
      </div>

      {mode === 'live' ? (
        <>
          {paused ? (
            <div className="feed feed-big feed-paused">
              <EyeOff size={26} />
              <span>Cameras paused for privacy</span>
            </div>
          ) : (
            <div className="player">
              <Feed cam={cam} big now={now} muted={muted} />
              {flash && <div className="flash" />}
              {cam.dog && !cam.offline && <span className="detect">{name} detected</span>}
            </div>
          )}

          <div className="player-meta">
            <div>
              <strong>{cam.name}</strong>
              <span>{cam.offline ? 'Last seen 2 hr ago' : cam.dog ? `${cam.room} · ${name} in view` : `${cam.room} · motion ${cam.motion}`}</span>
            </div>
          </div>

          <div className="controls">
            <button className={`ctrl ${talking ? 'is-on' : ''}`} onPointerDown={() => setTalking(true)} onPointerUp={() => setTalking(false)} onPointerLeave={() => setTalking(false)}>
              <Mic size={19} /><span>{talking ? 'Talking…' : 'Hold to talk'}</span>
            </button>
            <button className="ctrl" onClick={() => setMuted((m) => !m)}>
              {muted ? <VolumeX size={19} /> : <Volume2 size={19} />}<span>{muted ? 'Sound off' : 'Sound on'}</span>
            </button>
            <button className="ctrl" onClick={snap}>
              <CameraIcon size={19} /><span>Snapshot</span>
            </button>
            <button className={`ctrl ${recording ? 'is-rec' : ''}`} onClick={() => setRecording((r) => !r)}>
              <CircleDot size={19} /><span>{recording ? 'Recording' : 'Record'}</span>
            </button>
          </div>

          <section className="card">
            <div className="card-head">
              <h3 className="card-title">All cameras</h3>
              <span className="muted small">{CAMERAS.filter((c) => !c.offline).length} of {CAMERAS.length} online</span>
            </div>
            <div className="cam-grid">
              {CAMERAS.map((c) => (
                <button key={c.id} className={`cam-tile ${active === c.id ? 'is-on' : ''}`} onClick={() => setActive(c.id)}>
                  <Feed cam={c} now={now} />
                  <span className="cam-name">{c.name}</span>
                  <span className="cam-sub">{c.offline ? 'Offline' : c.dog ? `${name} here` : c.room}</span>
                </button>
              ))}
            </div>
          </section>

          <label className="card row privacy-row">
            <span>
              {paused ? <EyeOff size={15} className="inline-icon" /> : <Eye size={15} className="inline-icon" />}
              Pause all cameras
              <span className="row-sub">The hub light shows when someone is watching live</span>
            </span>
            <input type="checkbox" className="switch" checked={paused} onChange={(e) => setPaused(e.target.checked)} />
          </label>
        </>
      ) : (
        <section className="card">
          <div className="card-head">
            <h3 className="card-title">
              {recDate.toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' })}
            </h3>
          </div>
          {entry ? (
            <ul className="rec-list">
              {entry.clips.map(([time, label, src]) => (
                <li key={time}>
                  <div className="rec-thumb">
                    <img src={src} alt="" />
                    <span className="clip-play"><Play size={13} fill="currentColor" /></span>
                  </div>
                  <div className="rec-main">
                    <strong>{label}</strong>
                    <span>{time} · Laika hub · 0:{String(20 + label.length).slice(0, 2)}</span>
                  </div>
                  <button className="icon-btn icon-btn-sm" aria-label="Full screen"><Maximize2 size={15} /></button>
                </li>
              ))}
            </ul>
          ) : (
            <p className="muted small">No recordings this day. The hub was offline.</p>
          )}
        </section>
      )}
    </div>
  )
}
