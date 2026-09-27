import { ChevronRight, X } from 'lucide-react'
import Icon from './Icon'
import { SCREENS } from '../data'

const ITEMS = ['settings', 'camera', 'voice', 'help']

export default function MenuDrawer({ onSelect, onClose }) {
  return (
    <div className="overlay overlay-side" onClick={onClose}>
      <aside className="drawer" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-head">
          <div className="wordmark">laika</div>
          <button className="icon-btn" onClick={onClose} aria-label="Close menu">
            <X size={20} strokeWidth={1.75} />
          </button>
        </div>
        <ul className="drawer-list">
          {ITEMS.map((id) => (
            <li key={id}>
              <button onClick={() => onSelect(id)}>
                <span className="drawer-icon"><Icon name={SCREENS[id].icon} /></span>
                <span className="drawer-label">{SCREENS[id].title}</span>
                <ChevronRight size={18} className="muted" />
              </button>
            </li>
          ))}
        </ul>
        <div className="drawer-foot">Hub firmware 0.1 · Online</div>
      </aside>
    </div>
  )
}
