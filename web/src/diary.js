// Mock AI diary entries, written from the dog's point of view.
// In the real product these are generated nightly from verified hub and
// camera events; here we cycle through templates over recent dates.

const P = {
  a: '/photos/dog-6169.jpg',
  b: '/photos/dog-6168.jpg',
  c: '/photos/dog-6170.jpg',
}

const TEMPLATES = [
  {
    title: 'The Great Vacuum Incident',
    mood: 'Brave-ish',
    body: [
      'Dear diary,',
      'Today the loud floor monster came out again. I barked at it three times, which is the correct number. Then I retreated under the desk to supervise from a safe distance.',
      'My human said “it’s just the vacuum, {name}.” That is exactly what the vacuum would want them to think.',
      'After it went back into its cave, I booped the big green circle and the wall played my calm music. I did not need calm music. I listened to all of it anyway.',
      'Snack count: two. Should have been four.',
    ],
    clips: [['10:12 AM', 'Vacuum standoff', P.c], ['10:31 AM', 'Hiding under desk', P.b], ['10:40 AM', 'Booped for music', P.a]],
    stats: { walks: 2, naps: 3, treats: 2, boops: 6, barks: 9 },
    moments: 14,
  },
  {
    title: 'Jordan Came Early!!',
    mood: 'Zoomy',
    body: [
      'Dear diary,',
      'Jordan arrived at 12:52, which is eight minutes early and my favourite kind of early. I did four spins by the door. The wall wiggled its ears at Jordan too, so now we are both fans.',
      'We walked to the corner with the good smells. I found a leaf that smelled like a sandwich. Jordan said no.',
      'Back home I pulled the soft ring to say OUTSIDE AGAIN PLEASE, but the wall said not right now, very politely. I respect the wall. I will try again tomorrow.',
    ],
    clips: [['12:52 PM', 'Door spins', P.c], ['1:40 PM', 'Back from walk', P.a]],
    stats: { walks: 3, naps: 2, treats: 3, boops: 4, barks: 5 },
    moments: 11,
  },
  {
    title: 'A Very Important Nap',
    mood: 'Sleepy',
    body: [
      'Dear diary,',
      'I napped for most of the afternoon in my spot under the desk. It is the best spot because feet visit it.',
      'At 3:40 the wall offered tug. I accepted, obviously. I won. I think I won. It let go when I let go, which is suspicious but fair.',
      'Then a treat fell out of its little mouth onto the mat. I ate it before it could change its mind.',
      'Afterwards I napped again to recover from winning.',
    ],
    clips: [['2:15 PM', 'Desk nap', P.b], ['3:40 PM', 'Tug session', P.c], ['3:41 PM', 'Treat drop', P.a]],
    stats: { walks: 2, naps: 5, treats: 3, boops: 2, barks: 1 },
    moments: 9,
  },
  {
    title: 'Thunder Day',
    mood: 'Wobbly',
    body: [
      'Dear diary,',
      'The sky was grumbling all morning and I did not like it one bit. I stayed very close to my human’s ankles, which is my job during emergencies.',
      'The wall played its soft music without me even asking. I think the wall knows things.',
      'By dinner the sky had stopped being rude. I ate everything in my bowl, then checked the bowl twice more in case of a refill miracle.',
      'No miracle. Still brave.',
    ],
    clips: [['9:20 AM', 'Ankle duty', P.b], ['6:50 PM', 'Bowl inspection', P.a]],
    stats: { walks: 1, naps: 4, treats: 2, boops: 3, barks: 12 },
    moments: 8,
  },
  {
    title: 'The Hedgehog Situation',
    mood: 'Proud',
    body: [
      'Dear diary,',
      'My squeaky hedgehog went missing under the sofa for an entire morning. I searched. I sighed loudly. I stared at the sofa with great meaning.',
      'Nobody helped until 11:15, when my human finally got down on the floor and rescued him.',
      'I thanked them by squeaking him 47 times in a row. They said “okay, okay.” I think that means “more.”',
      'Tonight Hedgehog is sleeping next to me. We have been through a lot.',
    ],
    clips: [['9:05 AM', 'Staring at sofa', P.a], ['11:15 AM', 'The rescue', P.c]],
    stats: { walks: 2, naps: 3, treats: 4, boops: 5, barks: 3 },
    moments: 12,
  },
  {
    title: 'Guests!',
    mood: 'Social',
    body: [
      'Dear diary,',
      'Two new humans came over and BOTH of them smelled like other dogs. I had to investigate every sock thoroughly.',
      'One of them booped my nose, so I went to the wall and booped my big green circle back. Now everyone understands boops.',
      'I sat very nicely under the table during dinner. Nobody dropped anything. I have decided this was a mistake on their part, not mine.',
      'Guests are my favourite kind of weather.',
    ],
    clips: [['7:02 PM', 'Sock investigation', P.c], ['8:10 PM', 'Under-table duty', P.b]],
    stats: { walks: 2, naps: 2, treats: 3, boops: 8, barks: 6 },
    moments: 16,
  },
  {
    title: 'Bath Day (Rude)',
    mood: 'Damp',
    body: [
      'Dear diary,',
      'I was taken to the groomer today against my will. They washed me, fluffed me and put a bandana on me.',
      'I look extremely fancy. I am still upset.',
      'When I got home the wall wiggled one ear at me like it was impressed. It should be.',
      'I rolled on the rug for twenty minutes to get my smell back. Partial success.',
    ],
    clips: [['4:30 PM', 'Home, fluffy', P.a], ['4:36 PM', 'Rug rolling', P.b]],
    stats: { walks: 1, naps: 4, treats: 2, boops: 2, barks: 2 },
    moments: 7,
  },
  {
    title: 'Routine Report',
    mood: 'Content',
    body: [
      '7:00 — Woke up. Stretched both ends.',
      '7:30 — Walked. Sniffed a very interesting pole for longer than my human wanted.',
      '8:15 — Breakfast. Excellent. Gone too fast.',
      'Afternoon — Supervised laptop typing from under the desk.',
      '6:00 — Pulled the ring to say outside. It worked! My human said “good ask, {name}.” I am a good asker.',
      '10:00 — Bed. Tomorrow I will be good again, probably.',
    ],
    clips: [['1:20 PM', 'Desk supervision', P.b], ['6:00 PM', 'Asked for outside', P.c], ['9:55 PM', 'Bedtime', P.a]],
    stats: { walks: 3, naps: 3, treats: 2, boops: 4, barks: 2 },
    moments: 10,
  },
]

export const DAYS_BACK = 60

export function dateKey(d) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

export function startOfDay(d) {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate())
}

// Entry for a date, or null if the hub was offline that day.
export function entryFor(date) {
  const today = startOfDay(new Date())
  const daysAgo = Math.round((today - startOfDay(date)) / 86400000)
  if (daysAgo < 0 || daysAgo > DAYS_BACK) return null
  if (daysAgo % 9 === 5) return null
  return TEMPLATES[daysAgo % TEMPLATES.length]
}
