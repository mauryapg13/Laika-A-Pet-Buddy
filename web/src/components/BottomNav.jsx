import { BookOpen, House, Sparkles, User } from 'lucide-react'

const TABS = [
  { id: 'home', label: 'Home', Icon: House },
  { id: 'profile', label: 'Profile', Icon: User },
  { id: 'diary', label: 'Diary', Icon: BookOpen },
  { id: 'insights', label: 'Insights', Icon: Sparkles },
]

export default function BottomNav({ active, onChange }) {
  return (
    <nav className="bottomnav">
      {TABS.map(({ id, label, Icon }) => (
        <button
          key={id}
          className={`tab ${active === id ? 'is-active' : ''}`}
          onClick={() => onChange(id)}
        >
          <Icon size={22} strokeWidth={active === id ? 2 : 1.6} />
          <span>{label}</span>
        </button>
      ))}
    </nav>
  )
}
