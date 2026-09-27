// Mock "learned" behaviour data for the Insights screen.

export const HOURS = Array.from({ length: 18 }, (_, i) => i + 6) // 6 AM – 11 PM

// Likelihood 0–4 for each hour, learned from past weeks.
export const RHYTHM = [
  { id: 'play', label: 'Wants to play', values: [0, 0, 1, 1, 2, 1, 0, 0, 1, 2, 4, 3, 1, 1, 2, 1, 0, 0] },
  { id: 'out', label: 'Asks to go out', values: [3, 4, 1, 0, 0, 1, 2, 1, 0, 1, 3, 4, 1, 0, 1, 2, 3, 0] },
  { id: 'food', label: 'Food interest', values: [1, 2, 4, 1, 0, 0, 1, 1, 0, 1, 2, 2, 4, 3, 0, 0, 1, 0] },
  { id: 'idle', label: 'Awake & idle', values: [0, 0, 1, 2, 3, 2, 1, 3, 4, 3, 1, 0, 0, 1, 2, 2, 1, 0] },
  { id: 'nap', label: 'Napping', values: [1, 0, 0, 1, 1, 3, 4, 2, 1, 1, 0, 0, 0, 1, 1, 2, 3, 4] },
  { id: 'bark', label: 'Barking', values: [0, 1, 0, 0, 1, 0, 0, 0, 1, 1, 3, 1, 0, 0, 0, 1, 0, 0] },
]

export const LIKELIHOOD = ['Rarely', 'Sometimes', 'Often', 'Usually', 'Almost always']

// Awake-and-idle minutes, last 7 days (last value is today).
export const IDLE_WEEK = [150, 165, 95, 110, 80, 120, 85]
export const IDLE_USUAL = 110

export const RANGES = {
  today: {
    label: 'Today',
    summary: '{name} has been calm and steady today. One tug session at 11:15, two walks, and a longer nap than usual after lunch. The go-out request came right on schedule at 8:02.',
    events: 46,
  },
  week: {
    label: 'Week',
    summary: '{name} had a settled week. Play requests peaked on Thursday when Jordan visited, and go-out requests moved about 20 minutes earlier. Monday and Tuesday had long idle stretches in the early afternoon.',
    events: 312,
  },
  month: {
    label: 'Month',
    summary: 'Over the past month {name}’s routine has become more predictable. Meal and walk times barely vary, the hub is used 4–6 times a day, and repeat pulls after “not now” have dropped by half.',
    events: 1284,
  },
}

export const PREDICTIONS = [
  { time: '4:00 PM', window: '3:45 – 4:30', label: 'Likely to ask to go out', confidence: 0.86, icon: 'Trees' },
  { time: '4:30 PM', window: '4:15 – 5:15', label: 'Usually wants to play', confidence: 0.74, icon: 'Bone' },
  { time: '6:30 PM', window: '6:15 – 7:00', label: 'Food interest peaks', confidence: 0.81, icon: 'Cookie' },
]

export const PATTERNS = [
  { title: 'Plays more when Jordan visits', detail: '40% more play requests on walk-sitter days.' },
  { title: 'Go-out requests are getting earlier', detail: 'Average moved from 4:20 PM to 4:00 PM this week.' },
  { title: 'Barking clusters at 4:10 PM', detail: 'Short bursts most weekdays. Could be the mail delivery.' },
  { title: 'Fewer repeat pulls after “not now”', detail: 'Down from 3.1 to 1.4 per unavailable request.' },
]

export const BALANCE = [
  { label: 'Active', value: '3h 10m', delta: '+12 min', trend: 'up' },
  { label: 'Resting', value: '13h 5m', delta: 'Steady', trend: 'flat' },
  { label: 'Awake & idle', value: '2h 5m', delta: '+18%', trend: 'up' },
]

export const SUGGESTIONS = [
  {
    id: 'play-window',
    title: 'Move the Play window 30 min earlier?',
    detail: 'Play requests now start around 3:30 PM, but N4 opens at 4:00 PM.',
  },
  {
    id: 'afternoon-offer',
    title: 'Offer music after lunch on Mondays?',
    detail: 'Idle time on Mondays averages 2h 40m between 1 and 4 PM.',
  },
]
