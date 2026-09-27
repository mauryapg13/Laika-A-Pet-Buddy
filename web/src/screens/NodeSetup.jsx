import { useEffect, useState } from 'react'
import { Activity, Info, Minus, Plus, RefreshCw, RotateCcw, Zap } from 'lucide-react'
import HubDrawing from '../components/HubDrawing'
import Icon from '../components/Icon'
import {
  ACTIVITY, ATTACHMENTS, AVAILABILITY, CLASS_LABELS, CLASS_SUPPORTS, COOLDOWNS, CUES,
  DEFAULT_NODES, FUNCTIONS, NEEDS_LABELS, PAD_SLOT, SLOTS,
} from '../data'

const ALL_SLOTS = [PAD_SLOT, ...SLOTS]

// Full-screen setup for one node. Edits are held as drafts for every node,
// so you can hop between nodes and save everything at once.
export default function NodeSetup({ nodeId, nodes, dogName, onSwitch, onSave }) {
  const [drafts, setDrafts] = useState(nodes)
  const [toast, setToast] = useState(null)

  useEffect(() => {
    if (!toast) return
    const t = setTimeout(() => setToast(null), 2200)
    return () => clearTimeout(t)
  }, [toast])

  const slot = ALL_SLOTS.find((s) => s.id === nodeId)
  const draft = drafts[nodeId]
  const set = (patch) => setDrafts((d) => ({ ...d, [nodeId]: { ...d[nodeId], ...patch } }))
  const fn = draft.fn ? FUNCTIONS[draft.fn] : null
  const supports = CLASS_SUPPORTS[slot.cls]
  const att = ATTACHMENTS[nodeId]
  const activity = (draft.fn && ACTIVITY[draft.fn]) || []
  const dirty = JSON.stringify(drafts) !== JSON.stringify(nodes)
  const name = nodeId === 'boop' ? 'Boop pad' : nodeId

  return (
    <div className="setup">
      <div className="setup-scroll">
        <div className="setup-hero">
          <HubDrawing nodes={drafts} selected={nodeId} onSelect={onSwitch} focus />
        </div>

        <div className="node-tabs" role="tablist">
          {ALL_SLOTS.map((s) => {
            const f = drafts[s.id].fn && FUNCTIONS[drafts[s.id].fn]
            return (
              <button
                key={s.id}
                role="tab"
                aria-selected={s.id === nodeId}
                className={`node-tab ${s.id === nodeId ? 'is-on' : ''}`}
                onClick={() => onSwitch(s.id)}
              >
                <span className="node-tab-id">{s.id === 'boop' ? 'Boop' : s.id}</span>
                <span className="node-tab-fn">{f ? f.label : 'Empty'}</span>
              </button>
            )
          })}
        </div>

        <section className="card attach">
          <div className="attach-icon"><Zap size={18} /></div>
          <div className="attach-main">
            <div className="attach-name">{att.name}</div>
            <div className="attach-sub">{slot.name} · {CLASS_LABELS[slot.cls]} · {att.detail}</div>
          </div>
          <span className="pill">Connected</span>
          <div className="attach-cal">
            <span>{att.calibrated}</span>
            <button className="link-btn" onClick={() => setToast(`Recalibrating ${name}…`)}>
              <RefreshCw size={13} /> Recalibrate
            </button>
          </div>
        </section>

        <section className="card">
          <h3 className="card-title">What does {name} do?</h3>
          <div className="fn-grid">
            {Object.entries(FUNCTIONS).map(([id, f]) => {
              const ok = supports.includes(f.needs)
              return (
                <button
                  key={id}
                  className={`fn-chip tone-${f.tone} ${draft.fn === id ? 'is-on' : ''}`}
                  disabled={!ok}
                  onClick={() => set({ fn: id, confirm: f.forceConfirm || draft.confirm })}
                >
                  <Icon name={f.icon} size={18} />
                  <span className="fn-name">{f.label}</span>
                  {!ok && <span className="fn-why">{NEEDS_LABELS[f.needs]}</span>}
                </button>
              )
            })}
            <button className={`fn-chip tone-muted ${!draft.fn ? 'is-on' : ''}`} onClick={() => set({ fn: null })}>
              <span className="fn-name">Nothing</span>
            </button>
          </div>
          {fn && (
            <div className="fn-desc">
              <span className={`pill pill-${fn.tone}`}>{fn.mode}</span>
              <p>{fn.desc.replace('Pablo', dogName)}</p>
              {fn.note && <p className="note"><Info size={14} /> {fn.note}</p>}
            </div>
          )}
        </section>

        {fn && (
          <section className="card">
            <h3 className="card-title">When is it available?</h3>
            <div className="radio-list">
              {AVAILABILITY.map((a) => (
                <label key={a.id} className={`radio ${draft.availability === a.id ? 'is-on' : ''}`}>
                  <input
                    type="radio"
                    name="availability"
                    checked={draft.availability === a.id}
                    onChange={() => set({ availability: a.id })}
                  />
                  <span className="radio-mark" />
                  <span>
                    <span className="radio-label">{a.label}</span>
                    <span className="radio-sub">{a.sub.replace('Pablo', dogName)}</span>
                  </span>
                </label>
              ))}
            </div>
            {draft.availability === 'schedule' && (
              <div className="time-row">
                <label>From<input type="time" value={draft.from} onChange={(e) => set({ from: e.target.value })} /></label>
                <label>To<input type="time" value={draft.to} onChange={(e) => set({ to: e.target.value })} /></label>
              </div>
            )}
          </section>
        )}

        {fn && draft.availability !== 'off' && (
          <section className="card">
            <h3 className="card-title">Limits</h3>
            <div className="row">
              <span>{draft.fn === 'food' ? 'Treats per day' : 'Uses per day'}</span>
              <div className="stepper">
                <button onClick={() => set({ limit: Math.max(1, draft.limit - 1) })} aria-label="Fewer"><Minus size={16} /></button>
                <output>{draft.limit}</output>
                <button onClick={() => set({ limit: Math.min(20, draft.limit + 1) })} aria-label="More"><Plus size={16} /></button>
              </div>
            </div>
            <div className="row">
              <span>Rest between uses</span>
              <select value={draft.cooldown} onChange={(e) => set({ cooldown: Number(e.target.value) })}>
                {COOLDOWNS.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
              </select>
            </div>
            <label className="row">
              <span>
                Ask me to confirm first
                {fn.forceConfirm && <span className="row-sub">Required for {fn.label.toLowerCase()}</span>}
              </span>
              <input
                type="checkbox"
                className="switch"
                checked={draft.confirm || !!fn.forceConfirm}
                disabled={!!fn.forceConfirm}
                onChange={(e) => set({ confirm: e.target.checked })}
              />
            </label>
          </section>
        )}

        {fn && (
          <section className="card">
            <h3 className="card-title">How Laika responds</h3>
            {CUES.map((c) => (
              <label key={c.id} className="row">
                <span>
                  {c.label}
                  <span className="row-sub">{c.sub}</span>
                </span>
                <input
                  type="checkbox"
                  className="switch"
                  checked={draft.cues[c.id]}
                  onChange={(e) => set({ cues: { ...draft.cues, [c.id]: e.target.checked } })}
                />
              </label>
            ))}
          </section>
        )}

        {fn && (
          <section className="card">
            <h3 className="card-title"><Activity size={14} /> Today on {name}</h3>
            {activity.length ? (
              <ul className="timeline">
                {activity.map(([time, text]) => (
                  <li key={time + text}><time>{time}</time><span>{text}</span></li>
                ))}
              </ul>
            ) : (
              <p className="muted small">No activity yet today.</p>
            )}
          </section>
        )}

        <div className="setup-actions">
          <button className="btn btn-outline" onClick={() => setToast(`${name} is glowing on the hub`)}>
            <Zap size={16} /> Test node
          </button>
          <button className="link-btn danger" onClick={() => set(DEFAULT_NODES[nodeId])}>
            <RotateCcw size={13} /> Reset to default
          </button>
        </div>
      </div>

      {toast && <div className="toast">{toast}</div>}

      <div className="setup-foot">
        <button className="btn btn-primary" disabled={!dirty} onClick={() => onSave(drafts)}>
          {dirty ? 'Save changes' : 'Saved'}
        </button>
      </div>
    </div>
  )
}
