import { useEffect, useState } from 'react'
import TopBar from './components/TopBar'
import BottomNav from './components/BottomNav'
import MenuDrawer from './components/MenuDrawer'
import NotificationsSheet from './components/NotificationsSheet'
import Dashboard from './screens/Dashboard'
import NodeSetup from './screens/NodeSetup'
import Placeholder from './screens/Placeholder'
import Profile from './screens/Profile'
import Diary from './screens/Diary'
import Insights from './screens/Insights'
import VoiceTracking from './screens/VoiceTracking'
import CameraView from './screens/CameraView'
import Settings from './screens/Settings'
import Help from './screens/Help'
import { startOfDay } from './diary'
import { DEFAULT_NODES, DEFAULT_PROFILE, SCREENS } from './data'

const STORAGE_KEY = 'laika.nodes.v1'
const PROFILE_KEY = 'laika.profile.v3'

function loadNodes() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY))
    if (saved) {
      // Merge per node so newly added fields get their defaults.
      return Object.fromEntries(
        Object.entries(DEFAULT_NODES).map(([id, d]) => [id, { ...d, ...saved[id] }])
      )
    }
  } catch {}
  return DEFAULT_NODES
}

function loadProfile() {
  try {
    const saved = JSON.parse(localStorage.getItem(PROFILE_KEY))
    if (saved) return { ...DEFAULT_PROFILE, ...saved }
  } catch {}
  return DEFAULT_PROFILE
}

export default function App() {
  const [tab, setTab] = useState('home')
  const [menuScreen, setMenuScreen] = useState(null) // screen opened from the hamburger
  const [menuOpen, setMenuOpen] = useState(false)
  const [notifOpen, setNotifOpen] = useState(false)
  const [unread, setUnread] = useState(true)
  const [editing, setEditing] = useState(null) // node id being configured
  const [nodes, setNodes] = useState(loadNodes)
  const [profile, setProfile] = useState(loadProfile)
  const [diaryDate, setDiaryDate] = useState(() => startOfDay(new Date()))
  const [dayContext, setDayContext] = useState(null) // date passed from the diary to camera/insights

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(nodes))
  }, [nodes])

  useEffect(() => {
    // Uploaded photos can exceed the storage quota; the mockup keeps working either way.
    try { localStorage.setItem(PROFILE_KEY, JSON.stringify(profile)) } catch {}
  }, [profile])

  const current = menuScreen ?? tab

  return (
    <div className="stage">
      <div className="phone">
        <TopBar
          title={editing ? 'Node setup' : menuScreen && SCREENS[menuScreen].title}
          onBack={editing ? () => setEditing(null) : menuScreen ? () => setMenuScreen(null) : null}
          showActions={!editing}
          onBell={() => { setNotifOpen(true); setUnread(false) }}
          onMenu={() => setMenuOpen(true)}
          hasUnread={unread}
        />

        <main className={`screen ${editing ? 'screen-flush' : ''}`}>
          {editing ? (
            <NodeSetup
              nodeId={editing}
              nodes={nodes}
              dogName={profile.name}
              onSwitch={setEditing}
              onSave={(drafts) => { setNodes(drafts); setEditing(null) }}
            />
          ) : current === 'home' ? (
            <Dashboard
              nodes={nodes}
              profile={profile}
              onSelectNode={setEditing}
              onOpenProfile={() => setTab('profile')}
            />
          ) : current === 'profile' ? (
            <Profile profile={profile} onChange={setProfile} />
          ) : current === 'diary' ? (
            <Diary
              profile={profile}
              date={diaryDate}
              onDate={setDiaryDate}
              onOpenCamera={(d) => { setDayContext(d); setMenuScreen('camera') }}
              onOpenSummary={(d) => { setDayContext(d); setTab('insights') }}
            />
          ) : current === 'insights' ? (
            <Insights
              profile={profile}
              date={dayContext}
              onClearDate={() => setDayContext(null)}
              onOpenDiary={() => { setDiaryDate(dayContext); setDayContext(null); setTab('diary') }}
            />
          ) : current === 'camera' ? (
            <CameraView key={dayContext ? dayContext.toDateString() : 'live'} profile={profile} date={dayContext} />
          ) : current === 'settings' ? (
            <Settings profile={profile} onHelp={() => setMenuScreen('help')} />
          ) : current === 'help' ? (
            <Help profile={profile} />
          ) : current === 'voice' ? (
            <VoiceTracking profile={profile} />
          ) : (
            <Placeholder screen={SCREENS[current]} date={dayContext} />
          )}
        </main>

        {!editing && (
          <BottomNav
            active={menuScreen ? null : tab}
            onChange={(id) => { setTab(id); setMenuScreen(null); setDayContext(null) }}
          />
        )}

        {menuOpen && (
          <MenuDrawer
            onClose={() => setMenuOpen(false)}
            onSelect={(id) => { setMenuScreen(id); setMenuOpen(false); setDayContext(null) }}
          />
        )}
        {notifOpen && <NotificationsSheet onClose={() => setNotifOpen(false)} />}
      </div>
    </div>
  )
}
