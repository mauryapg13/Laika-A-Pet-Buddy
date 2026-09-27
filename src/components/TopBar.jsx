import { Bell, ChevronLeft, Menu } from 'lucide-react'

export default function TopBar({ title, onBack, onBell, onMenu, hasUnread, showActions = true }) {
  return (
    <header className="topbar">
      {onBack ? (
        <button className="icon-btn" onClick={onBack} aria-label="Back">
          <ChevronLeft size={22} strokeWidth={1.75} />
        </button>
      ) : (
        <div className="wordmark">laika</div>
      )}
      {onBack && <h1 className="topbar-title">{title}</h1>}
      {showActions && (
      <div className="topbar-actions">
        <button className="icon-btn" onClick={onBell} aria-label="Notifications">
          <Bell size={21} strokeWidth={1.75} />
          {hasUnread && <span className="dot" />}
        </button>
        <button className="icon-btn" onClick={onMenu} aria-label="Menu">
          <Menu size={22} strokeWidth={1.75} />
        </button>
      </div>
      )}
    </header>
  )
}
