import { useState } from 'react'
import { IDLE_USUAL, IDLE_WEEK } from '../insights'

const W = 320
const H = 130
const TOP = 12
const BASE = 104 // baseline y
const MAX = 180 // minutes at the top of the scale

const fmt = (m) => `${Math.floor(m / 60)}h ${m % 60}m`
const y = (m) => BASE - (m / MAX) * (BASE - TOP)

export default function IdleBars() {
  const today = new Date()
  const days = IDLE_WEEK.map((m, i) => {
    const d = new Date(today.getFullYear(), today.getMonth(), today.getDate() - (IDLE_WEEK.length - 1 - i))
    return { m, label: d.toLocaleDateString('en-US', { weekday: 'short' }), isToday: i === IDLE_WEEK.length - 1 }
  })
  const [active, setActive] = useState(days.length - 1)
  const slot = W / days.length
  const barW = 22

  return (
    <div className="bars">
      <div className="heat-readout">
        <strong>{days[active].isToday ? 'Today so far' : days[active].label}</strong>
        <span>{fmt(days[active].m)} awake & idle · usual {fmt(IDLE_USUAL)}</span>
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} className="bars-svg" role="img" aria-label="Awake and idle time, last 7 days">
        {days.map((d, i) => {
          const x = i * slot + (slot - barW) / 2
          const top = y(d.m)
          return (
            <g
              key={i}
              onMouseEnter={() => setActive(i)}
              onClick={() => setActive(i)}
              className="bar-hit"
            >
              <rect x={i * slot} y={0} width={slot} height={H} fill="transparent" />
              <path
                d={`M${x} ${BASE} V${top + 4} Q${x} ${top} ${x + 4} ${top} H${x + barW - 4} Q${x + barW} ${top} ${x + barW} ${top + 4} V${BASE} Z`}
                className={`bar ${d.isToday ? 'is-today' : ''} ${active === i ? 'is-on' : ''}`}
              />
              <text x={i * slot + slot / 2} y={H - 8} textAnchor="middle" className={`bar-label ${active === i ? 'is-on' : ''}`}>
                {d.label}
              </text>
            </g>
          )
        })}
        <line x1="0" x2={W} y1={BASE} y2={BASE} className="bar-base" />
        <line x1="0" x2={W} y1={y(IDLE_USUAL)} y2={y(IDLE_USUAL)} className="bar-usual" />
        <text x={W} y={y(IDLE_USUAL) - 5} textAnchor="end" className="bar-usual-label">usual</text>
      </svg>
    </div>
  )
}
