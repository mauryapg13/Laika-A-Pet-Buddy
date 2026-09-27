import { useState } from 'react'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import Sheet from './Sheet'
import { DAYS_BACK, dateKey, entryFor, startOfDay } from '../diary'

const WEEKDAYS = ['S', 'M', 'T', 'W', 'T', 'F', 'S']

export default function CalendarSheet({ selected, onPick, onClose }) {
  const today = startOfDay(new Date())
  const earliest = new Date(today.getFullYear(), today.getMonth(), today.getDate() - DAYS_BACK)
  const [month, setMonth] = useState(new Date(selected.getFullYear(), selected.getMonth(), 1))

  const first = month.getDay()
  const daysInMonth = new Date(month.getFullYear(), month.getMonth() + 1, 0).getDate()
  const cells = [...Array(first).fill(null), ...Array.from({ length: daysInMonth }, (_, i) => i + 1)]
  const canPrev = month > new Date(earliest.getFullYear(), earliest.getMonth(), 1)
  const canNext = month < new Date(today.getFullYear(), today.getMonth(), 1)
  const shift = (n) => setMonth(new Date(month.getFullYear(), month.getMonth() + n, 1))

  return (
    <Sheet title="Pick a day" kicker="Diary" onClose={onClose}>
      <div className="cal-head">
        <button className="icon-btn" onClick={() => shift(-1)} disabled={!canPrev} aria-label="Previous month">
          <ChevronLeft size={20} />
        </button>
        <span>{month.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}</span>
        <button className="icon-btn" onClick={() => shift(1)} disabled={!canNext} aria-label="Next month">
          <ChevronRight size={20} />
        </button>
      </div>
      <div className="cal-grid">
        {WEEKDAYS.map((w, i) => <span key={i} className="cal-wd">{w}</span>)}
        {cells.map((day, i) => {
          if (!day) return <span key={`e${i}`} />
          const d = new Date(month.getFullYear(), month.getMonth(), day)
          const inRange = d <= today && d >= earliest
          const has = inRange && !!entryFor(d)
          const isSel = dateKey(d) === dateKey(selected)
          const isToday = dateKey(d) === dateKey(today)
          return (
            <button
              key={day}
              className={`cal-day ${isSel ? 'is-on' : ''} ${isToday ? 'is-today' : ''} ${has ? 'has-entry' : ''}`}
              disabled={!inRange}
              onClick={() => onPick(d)}
            >
              {day}
            </button>
          )
        })}
      </div>
      <p className="cal-legend"><span className="cal-dot" /> Diary entry written</p>
    </Sheet>
  )
}
