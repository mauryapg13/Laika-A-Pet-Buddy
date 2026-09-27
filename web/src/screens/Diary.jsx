import { useEffect, useRef, useState } from 'react'
import { CalendarDays, ChevronLeft, ChevronRight, Play, Printer, Sparkles, Video } from 'lucide-react'
import CalendarSheet from '../components/CalendarSheet'
import PawPrint from '../components/PawPrint'
import { DAYS_BACK, dateKey, entryFor, startOfDay } from '../diary'

const STAT_LABELS = [
  ['walks', 'Walks'], ['naps', 'Naps'], ['treats', 'Treats'], ['boops', 'Boops'], ['barks', 'Barks'],
]

export default function Diary({ profile, date, onDate, onOpenCamera, onOpenSummary }) {
  const [calOpen, setCalOpen] = useState(false)
  const stripRef = useRef(null)
  const today = startOfDay(new Date())
  const days = Array.from({ length: DAYS_BACK + 1 }, (_, i) =>
    new Date(today.getFullYear(), today.getMonth(), today.getDate() - DAYS_BACK + i))
  const entry = entryFor(date)
  const idx = days.findIndex((d) => dateKey(d) === dateKey(date))
  const fill = (s) => s.replaceAll('{name}', profile.name)

  // Keep the selected day visible in the strip.
  useEffect(() => {
    stripRef.current?.querySelector('.is-on')?.scrollIntoView({ inline: 'center', block: 'nearest' })
  }, [date])

  const longDate = date.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })

  return (
    <div className="diary">
      <div className="diary-head">
        <h1>{date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}</h1>
        <button className="btn-chip" onClick={() => setCalOpen(true)}>
          <CalendarDays size={15} /> Pick date
        </button>
      </div>

      <div className="date-strip" ref={stripRef}>
        {days.map((d) => (
          <button
            key={dateKey(d)}
            className={`date-chip ${dateKey(d) === dateKey(date) ? 'is-on' : ''}`}
            onClick={() => onDate(d)}
          >
            <span className="date-wd">{d.toLocaleDateString('en-US', { weekday: 'short' })}</span>
            <span className="date-num">{d.getDate()}</span>
            <span className={`date-dot ${entryFor(d) ? '' : 'is-empty'}`} />
          </button>
        ))}
      </div>

      {entry ? (
        <>
          <article className="diary-page">
            <div className="page-top">
              <span className="page-date">{longDate}</span>
              <span className="mood">feeling: {entry.mood}</span>
            </div>
            <figure className="polaroid">
              <span className="tape" />
              <img src={entry.clips[0][2]} alt="" />
              <figcaption>{entry.clips[0][1].toLowerCase()}</figcaption>
            </figure>
            <h2 className="page-title">{entry.title}</h2>
            <div className="page-body">
              {entry.body.map((p, i) => <p key={i}>{fill(p)}</p>)}
            </div>
            <div className="signoff">
              <span>Love, {profile.name}</span>
              <PawPrint size={46} className="paw" />
            </div>
            <p className="page-source">
              <Sparkles size={12} /> Written by Laika from {entry.moments} moments caught on camera
            </p>
          </article>

          <div className="page-nav">
            <button className="icon-btn" disabled={idx <= 0} onClick={() => onDate(days[idx - 1])} aria-label="Previous day">
              <ChevronLeft size={20} />
            </button>
            <button className="btn-chip" onClick={() => window.print()}>
              <Printer size={15} /> Print entry
            </button>
            <button className="icon-btn" disabled={idx >= days.length - 1} onClick={() => onDate(days[idx + 1])} aria-label="Next day">
              <ChevronRight size={20} />
            </button>
          </div>

          <section className="card">
            <div className="card-head">
              <h3 className="card-title"><Video size={14} /> From the camera</h3>
              <button className="link-btn" onClick={() => onOpenCamera(date)}>Open feed <ChevronRight size={14} /></button>
            </div>
            <div className="clips">
              {entry.clips.map(([time, label, src]) => (
                <button key={time} className="clip" onClick={() => onOpenCamera(date)}>
                  <img src={src} alt="" />
                  <span className="clip-play"><Play size={14} fill="currentColor" /></span>
                  <span className="clip-time">{time}</span>
                  <span className="clip-label">{label}</span>
                </button>
              ))}
            </div>
          </section>

          <section className="card">
            <div className="card-head">
              <h3 className="card-title"><Sparkles size={14} /> Day at a glance</h3>
            </div>
            <div className="glance">
              {STAT_LABELS.map(([k, label]) => (
                <div key={k}><strong>{entry.stats[k]}</strong><span>{label}</span></div>
              ))}
            </div>
            <button className="btn btn-outline glance-btn" onClick={() => onOpenSummary(date)}>
              See full day summary
            </button>
          </section>
        </>
      ) : (
        <div className="diary-empty">
          <PawPrint size={40} className="paw-faded" />
          <h2>No entry for {longDate}</h2>
          <p>Laika was offline this day, so {profile.name} had nothing to write about.</p>
        </div>
      )}

      {calOpen && (
        <CalendarSheet
          selected={date}
          onClose={() => setCalOpen(false)}
          onPick={(d) => { onDate(d); setCalOpen(false) }}
        />
      )}
    </div>
  )
}
