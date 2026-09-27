import { useState } from 'react'

const W = 320
const H = 110
const TOP = 16
const BASE = 84

// Single-series 7-day bar chart with a tap/hover readout. Last value is today.
export default function WeekBars({ values, tone = 'sage', unit }) {
  const today = new Date()
  const days = values.map((v, i) => {
    const d = new Date(today.getFullYear(), today.getMonth(), today.getDate() - (values.length - 1 - i))
    return { v, label: d.toLocaleDateString('en-US', { weekday: 'short' }), isToday: i === values.length - 1 }
  })
  const [active, setActive] = useState(days.length - 1)
  const max = Math.max(...values) * 1.15
  const slot = W / days.length
  const barW = 20
  const y = (v) => BASE - (v / max) * (BASE - TOP)
  const a = days[active]

  return (
    <div className={`wbars tone-${tone}`}>
      <svg viewBox={`0 0 ${W} ${H}`} className="bars-svg" role="img" aria-label={`${unit} per day, last 7 days`}>
        {days.map((d, i) => {
          const x = i * slot + (slot - barW) / 2
          const top = y(d.v)
          return (
            <g key={i} className="bar-hit" onMouseEnter={() => setActive(i)} onClick={() => setActive(i)}>
              <rect x={i * slot} y={0} width={slot} height={H} fill="transparent" />
              <path
                d={`M${x} ${BASE} V${top + 4} Q${x} ${top} ${x + 4} ${top} H${x + barW - 4} Q${x + barW} ${top} ${x + barW} ${top + 4} V${BASE} Z`}
                className={`wbar ${active === i ? 'is-on' : ''}`}
              />
              {active === i && (
                <text x={x + barW / 2} y={top - 5} textAnchor="middle" className="wbar-value">{d.v}</text>
              )}
              <text x={i * slot + slot / 2} y={H - 6} textAnchor="middle" className={`bar-label ${active === i ? 'is-on' : ''}`}>
                {d.isToday ? 'Today' : d.label}
              </text>
            </g>
          )
        })}
        <line x1="0" x2={W} y1={BASE} y2={BASE} className="bar-base" />
      </svg>
      <p className="wbars-readout">{a.isToday ? 'Today' : a.label}: {a.v} {unit}</p>
    </div>
  )
}
