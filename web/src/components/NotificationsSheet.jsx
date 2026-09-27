import Sheet from './Sheet'
import { NOTIFICATIONS } from '../data'

export default function NotificationsSheet({ onClose }) {
  return (
    <Sheet title="Notifications" kicker="Today" onClose={onClose}>
      <ul className="notif-list">
        {NOTIFICATIONS.map((n) => (
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
