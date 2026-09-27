import {
  Bone, BookOpen, CircleHelp, Cookie, Dog, Heart, Mic, Moon, Music,
  Settings, Sparkles, Trees, User, Video,
} from 'lucide-react'

// Lets data.js refer to icons by name.
const ICONS = { Bone, BookOpen, CircleHelp, Cookie, Dog, Heart, Mic, Moon, Music, Settings, Sparkles, Trees, User, Video }

export default function Icon({ name, size = 20, ...rest }) {
  const Cmp = ICONS[name]
  return Cmp ? <Cmp size={size} strokeWidth={1.75} {...rest} /> : null
}
