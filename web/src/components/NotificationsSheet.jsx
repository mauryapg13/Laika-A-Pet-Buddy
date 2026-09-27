import Sheet from './Sheet'
import { NOTIFICATIONS } from '../data'
import { parseNotification } from '../api'

// Live: the hub's own notifications (factual, newest first). Mock list when the back end is off.
export default function NotificationsSheet({ laika, name, onClose }) {
  const live = laika?.connected ? laika.live.hub.notifications : null
  const items = live
    ? live.slice().reverse().map((n, i) => ({ id: i, ...parseNotification(n, name), tone: 'sage' }))
    : NOTIFICATIONS

  return (
    <Sheet title="Notifications" kicker={live ? 'Live from Laika' : 'Today'} onClose={onClose}>
      {live && !live.length && <p className="muted small">Nothing yet today. Laika will tell you when {name} asks for something.</p>}
      <ul className="notif-list">
        {items.map((n) => (
          <li key={n.id} className="notif">
            <span className={`notif-dot tone-${n.tone}`} />
            <div>
              <p>{n.text}</p>
              <time>{n.time}</time>
            </div>
          </li>
        ))}
      </ul>
    </Sheet>
  )
}
