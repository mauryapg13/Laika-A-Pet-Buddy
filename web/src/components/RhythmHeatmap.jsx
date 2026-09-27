import { useState } from 'react'
import { HOURS, LIKELIHOOD, RHYTHM } from '../insights'

// Single-hue sequential scale (sage), light → dark = less → more likely.
const STEPS = ['#eef2ea', '#d3dfcc', '#a9c09f', '#7f9d74', '#56704f']

function hourLabel(h) {
  const hr = h % 12 || 12
  return `${hr} ${h < 12 ? 'AM' : 'PM'}`
}

export default function RhythmHeatmap() {
  const [active, setActive] = useState({ row: 0, col: 10 })
  const nowHour = new Date().getHours()
  const nowCol = HOURS.indexOf(nowHour)
  const row = RHYTHM[active.row]
  const h = HOURS[active.col]

  return (
    <div className="heat">
      <div className="heat-readout" aria-live="polite">
        <strong>{row.label}</strong>
        <span>{hourLabel(h)} – {hourLabel(h + 1)} · {LIKELIHOOD[row.values[active.col]]}</span>
      </div>

      <div className="heat-grid" style={{ '--cols': HOURS.length }}>
        {RHYTHM.map((r, ri) => (
          <div key={r.id} className="heat-row">
            <span className="heat-label">{r.label}</span>
            <div className="heat-cells">
              {r.values.map((v, ci) => (
                <button
                  key={ci}
                  className={`heat-cell ${active.row === ri && active.col === ci ? 'is-on' : ''} ${ci === nowCol ? 'is-now' : ''}`}
                  style={{ background: STEPS[v] }}
                  onMouseEnter={() => setActive({ row: ri, col: ci })}
                  onFocus={() => setActive({ row: ri, col: ci })}
                  onClick={() => setActive({ row: ri, col: ci })}
                  aria-label={`${r.label}, ${hourLabel(HOURS[ci])}: ${LIKELIHOOD[v]}`}
                />
              ))}
            </div>
          </div>
        ))}
        <div className="heat-row heat-axis">
          <span className="heat-label" />
          <div className="heat-cells">
            {HOURS.map((hr, i) => (
              <span key={hr} className={i === nowCol ? 'is-now' : ''}>
                {i % 3 === 0 ? (hr % 12 || 12) + (hr < 12 ? 'a' : 'p') : i === nowCol ? 'now' : ''}
              </span>
            ))}
          </div>
        </div>
      </div>

      <div className="heat-legend">
        <span>Less likely</span>
        {STEPS.map((c) => <i key={c} style={{ background: c }} />)}
        <span>More likely</span>
      </div>
    </div>
  )
}
