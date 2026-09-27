// Mock data for the prototype. No real hub or backend yet.

export const DOG = { name: 'Pablo' }

export const DEFAULT_PROFILE = {
  name: 'Pablo',
  breed: 'Shih Tzu',
  birthday: '2020-03-08',
  sex: 'Male',
  neutered: true,
  weight: 7,
  size: 'Small',
  coat: 'Long, white and brown',
  photo: '/photos/dog-6169.jpg',
  tagline: 'Small dog, big opinions. Happiest under a desk at someone’s feet.',
  traits: { energy: 3, people: 5, dogs: 3, play: 4, food: 5, independence: 2, vocal: 3, noise: 4 },
  tags: ['Cuddly', 'Food-motivated', 'Velcro dog', 'Stubborn', 'Goofy'],
  favourites: { toy: 'Squeaky hedgehog', treat: 'Salmon bites', game: 'Gentle tug', spot: 'Under the desk' },
  fears: ['Thunder', 'Vacuum', 'Skateboards'],
  cues: ['Sit', 'Wait', 'Drop it', 'Leave it', 'Paw', 'Release'],
  safety: { guarding: false, chewer: true, fixation: false, mobility: false },
  routine: [
    ['7:00', 'Wake up + garden'],
    ['7:30', 'Morning walk · 20 min'],
    ['8:15', 'Breakfast'],
    ['13:00', 'Short walk with Jordan'],
    ['18:00', 'Evening walk + play'],
    ['18:45', 'Dinner'],
    ['22:00', 'Bedtime'],
  ],
  health: [
    ['Vet', 'Riverside Animal Clinic'],
    ['Vaccinations', 'Up to date · due Mar 2027'],
    ['Grooming', 'Every 6 weeks · next Oct 12'],
    ['Allergies', 'Chicken'],
    ['Medication', 'None'],
    ['Microchip', '•••• 4821'],
  ],
  gallery: ['/photos/dog-6169.jpg', '/photos/dog-6168.jpg', '/photos/dog-6170.jpg'],
}

export const TRAITS = [
  { id: 'energy', label: 'Energy', low: 'Couch potato', high: 'Always on' },
  { id: 'people', label: 'With people', low: 'Reserved', high: 'Loves everyone' },
  { id: 'dogs', label: 'With other dogs', low: 'Selective', high: 'Social butterfly' },
  { id: 'play', label: 'Playfulness', low: 'Laid back', high: 'Play-obsessed' },
  { id: 'food', label: 'Food drive', low: 'Picky', high: 'Anything for a treat' },
  { id: 'independence', label: 'Independence', low: 'Velcro', high: 'Does own thing' },
  { id: 'vocal', label: 'Barking', low: 'Quiet', high: 'Chatty' },
  { id: 'noise', label: 'Noise sensitivity', low: 'Unbothered', high: 'Startles easily' },
]

export const TAG_OPTIONS = [
  'Gentle', 'Playful', 'Curious', 'Cuddly', 'Calm', 'Clever', 'Goofy', 'Shy', 'Stubborn',
  'Protective', 'Food-motivated', 'Velcro dog', 'Independent', 'Loves tug', 'Nose-first',
  'Easily excited', 'Anxious alone', 'Couch potato',
]

// PRD §3 / §11.1: these affect what the hub is allowed to offer.
export const SAFETY = [
  { id: 'guarding', label: 'Guards toys or food' },
  { id: 'chewer', label: 'Strong chewer' },
  { id: 'fixation', label: 'Fixates on pulling' },
  { id: 'mobility', label: 'Joint or mobility issues' },
]

export const SIZES = ['Small', 'Medium', 'Large', 'Giant']

// What each kind of node hardware can do (PRD §7.2).
export const CLASS_SUPPORTS = {
  pad: ['input'],
  resistance: ['resistance', 'input'],
  input: ['input'],
  output: ['output'],
}

export const CLASS_LABELS = {
  pad: 'Central boop pad',
  resistance: 'Pull node',
  input: 'Touch node',
  output: 'Output node',
}

export const NEEDS_LABELS = {
  resistance: 'Needs a pull node',
  input: 'Needs a touch or pull node',
  output: 'Needs the output node',
}

// Physical slots on the hub. x/y are positions in the drawing.
export const SLOTS = [
  { id: 'N1', name: 'Upper left', cls: 'resistance', x: 112, y: 140, side: 'left' },
  { id: 'N2', name: 'Upper right', cls: 'input', x: 248, y: 140, side: 'right' },
  { id: 'N3', name: 'Right', cls: 'input', x: 266, y: 225, side: 'right' },
  { id: 'N4', name: 'Lower right', cls: 'resistance', x: 232, y: 300, side: 'right' },
  { id: 'N5', name: 'Lower left', cls: 'output', x: 128, y: 300, side: 'left' },
]

export const PAD_SLOT = { id: 'boop', name: 'Center', cls: 'pad' }

export const FUNCTIONS = {
  play: {
    label: 'Play',
    icon: 'Bone',
    needs: 'resistance',
    tone: 'sage',
    mode: 'Play session',
    desc: 'A short tug session with gentle, capped resistance.',
    note: 'When Play is off, the strap retracts. It never just gets harder to pull.',
  },
  outside: {
    label: 'Go out',
    icon: 'Trees',
    needs: 'input',
    tone: 'sage',
    mode: 'Request',
    desc: 'Pablo asks to go outside and you get one notification.',
    note: 'Pulling harder or more often never makes the request more urgent.',
  },
  attention: {
    label: 'Attention',
    icon: 'Heart',
    needs: 'input',
    tone: 'sage',
    mode: 'Request',
    desc: 'Asks for someone to come over.',
  },
  rest: {
    label: 'Rest',
    icon: 'Moon',
    needs: 'input',
    tone: 'sage',
    mode: 'Choice',
    desc: 'Lets Pablo ask for quiet time.',
  },
  music: {
    label: 'Music',
    icon: 'Music',
    needs: 'input',
    tone: 'sage',
    mode: 'Toggle',
    desc: 'Starts or stops calming audio. Press again to stop.',
  },
  food: {
    label: 'Food',
    icon: 'Cookie',
    needs: 'output',
    tone: 'ochre',
    mode: 'Output',
    desc: 'Drops one treat onto the mat.',
    note: 'Every drop is sensor-checked and capped per day.',
  },
  walk: {
    label: 'Walk',
    icon: 'Dog',
    needs: 'output',
    tone: 'ochre',
    mode: 'Output',
    desc: 'Releases the harness onto the mat.',
    note: 'Always needs someone at home to confirm first.',
    forceConfirm: true,
  },
}

export const AVAILABILITY = [
  { id: 'off', label: 'Off', sub: 'Parked and hidden from Pablo' },
  { id: 'manual', label: 'When I offer it', sub: 'You turn it on from the app' },
  { id: 'schedule', label: 'On a schedule', sub: 'Available during set hours' },
  { id: 'home', label: "When someone's home", sub: 'Only while a person is in' },
]

export const COOLDOWNS = [
  { value: 30, label: '30 sec' },
  { value: 120, label: '2 min' },
  { value: 300, label: '5 min' },
  { value: 900, label: '15 min' },
  { value: 3600, label: '1 hour' },
]

const base = {
  availability: 'manual', limit: 10, cooldown: 120, confirm: false, from: '08:00', to: '20:00',
  cues: { light: true, sound: true, ears: true },
}

export const DEFAULT_NODES = {
  boop: { ...base, fn: 'music', cooldown: 30 },
  N1: { ...base, fn: null, availability: 'off' },
  N2: { ...base, fn: 'outside', availability: 'home' },
  N3: { ...base, fn: 'rest' },
  N4: { ...base, fn: 'play', availability: 'schedule', limit: 4, from: '16:00', to: '19:00' },
  N5: { ...base, fn: 'food', limit: 6, cooldown: 900 },
}

// What's physically plugged into each slot (mock, PRD §7.3).
export const ATTACHMENTS = {
  boop: { name: 'Boop pad', detail: 'Built in', calibrated: 'Calibrated 2 days ago' },
  N1: { name: 'Owner button', detail: 'Rev A', calibrated: 'Calibrated 5 days ago' },
  N2: { name: 'Soft ring', detail: 'Rev B', calibrated: 'Calibrated 2 days ago' },
  N3: { name: 'Fabric tab', detail: 'Rev A', calibrated: 'Calibrated 2 days ago' },
  N4: { name: 'Tug strap', detail: 'Rev B · 1,204 pulls', calibrated: 'Calibrated yesterday' },
  N5: { name: 'Treat dispenser', detail: 'Rev A · 62% full', calibrated: 'Calibrated today' },
}

export const CUES = [
  { id: 'light', label: 'Light halo', sub: 'Soft glow around the node' },
  { id: 'sound', label: 'Chime', sub: 'Short, quiet confirmation sound' },
  { id: 'ears', label: 'Ear wiggle', sub: 'One slow ear lift' },
]

// Today's activity per function (mock).
export const ACTIVITY = {
  play: [['3:40 PM', 'Tug session · 42 sec'], ['11:15 AM', 'Tug session · 1 min 5 sec']],
  outside: [['4:12 PM', 'Asked to go out · you responded'], ['8:02 AM', 'Asked to go out']],
  attention: [['1:30 PM', 'Asked for attention']],
  rest: [['2:48 PM', 'Chose rest']],
  music: [['12:10 PM', 'Music on · 25 min'], ['9:40 AM', 'Music on · 12 min']],
  food: [['3:41 PM', 'One treat dropped'], ['11:16 AM', 'One treat dropped'], ['11:30 AM', 'Drop not confirmed']],
  walk: [['8:05 AM', 'Harness released · confirmed by you']],
}

export const NOTIFICATIONS = [
  { id: 1, time: '4:12 PM', text: 'Pablo selected Go out.', tone: 'sage' },
  { id: 2, time: '3:40 PM', text: 'The tug session ended after 42 seconds.', tone: 'sage' },
  { id: 3, time: '2:05 PM', text: 'Three repeated pulls happened while Go out was off.', tone: 'muted' },
  { id: 4, time: '11:30 AM', text: 'A treat was requested but not confirmed. Check the dispenser.', tone: 'ochre' },
  { id: 5, time: '9:02 AM', text: 'Laika came back online.', tone: 'muted' },
]

// Placeholder screens until each one is built.
export const SCREENS = {
  profile: { title: 'Profile', icon: 'User', blurb: "Pablo's details, personality, behaviours and photos." },
  diary: { title: 'Diary', icon: 'BookOpen', blurb: 'Daily entries you can read, track and print.' },
  insights: { title: 'Insights', icon: 'Sparkles', blurb: 'Activity data and an AI summary of Pablo’s day.' },
  settings: { title: 'Settings', icon: 'Settings', blurb: 'Account, hub, privacy and notification settings.' },
  camera: { title: 'Camera view', icon: 'Video', blurb: 'Live view and recorded clips from the hub.' },
  voice: { title: 'Voice tracking', icon: 'Mic', blurb: 'Bark and sound events picked up by the hub.' },
  help: { title: 'Help', icon: 'CircleHelp', blurb: 'Guides, training tips and support.' },
}
