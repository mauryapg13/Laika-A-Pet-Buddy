# Laika · Owner web app (hi-fi clickable mockup)

Mobile-first web app for the Laika hub. On a phone it runs fullscreen; on a laptop it shows inside a phone frame.
Everything runs on **mock data**. No back end is connected yet. This README explains where each screen's data
comes from today and which device-model API endpoint should replace it.

## Run it

Requires Node 18+.

```bash
npm install
npm run dev        # http://localhost:5173 (also shows a Network URL to open on your phone)
npm run build      # production build in dist/
```

## Screens

| Screen | Where | File |
|---|---|---|
| Home / dashboard (3D hub drawing, tap a node) | bottom nav | `src/screens/Dashboard.jsx`, `src/components/HubDrawing.jsx` |
| Node setup (function, availability, limits, cues) | tap any node | `src/screens/NodeSetup.jsx` |
| Profile (photo, breed, temperament, safety flags) | bottom nav | `src/screens/Profile.jsx` |
| Diary (handwritten AI entry, date picker, print) | bottom nav | `src/screens/Diary.jsx` |
| Insights (AI summary, daily rhythm, predictions, boredom buster) | bottom nav | `src/screens/Insights.jsx` |
| Camera view (multi-camera live + recordings) | hamburger | `src/screens/CameraView.jsx` |
| Voice tracking (owner interactions + bark activations) | hamburger | `src/screens/VoiceTracking.jsx` |
| Settings (household, hub, safety/emergency stop, privacy) | hamburger | `src/screens/Settings.jsx` |
| Help (training plan, cue guide, FAQ, contact) | hamburger | `src/screens/Help.jsx` |

Not built yet: onboarding and a full notifications screen (notifications are currently a bottom sheet).

## Mock data → device-model API

The device model (`api/server.py` in the Laika-A-Pet-Buddy repo) exposes `POST /input`, `GET /state`,
`GET /summary`, `GET /events` and `GET /layout`. Suggested wiring:

| UI | Mock source today | Replace with |
|---|---|---|
| Hub drawing: node states, labels | `SLOTS`, `DEFAULT_NODES` in `src/data.js` | `GET /layout` for labels, poll `GET /state` (~1 s) for `nodes`, `ears`, `halo` |
| Node setup: Save | `localStorage` (`laika.nodes.v1`) | `POST /input` with owner actions (`offer` / `park` per feature) |
| Notifications sheet | `NOTIFICATIONS` in `src/data.js` | `notifications` from `GET /state` |
| Diary entries + clips | `src/diary.js` | output of the `diary/` module |
| Insights + diary "day summary" | `src/insights.js`, `entryFor()` in `src/diary.js` | `GET /summary?day=YYYY-MM-DD` |
| Voice tracking log | `LOG` in `src/screens/VoiceTracking.jsx` | `BARK_EVENT` + owner events from `GET /events` |
| Camera view | static photos in `public/photos/` | `camera/` module streams / clips |
| Emergency stop (Settings → Safety) | local state | `POST /input` `{"type":"owner","action":"stop"}`, then `reset` |
| Profile | `DEFAULT_PROFILE` in `src/data.js`, `localStorage` | new endpoint (not in the device model yet) |

### Known differences to reconcile

- **Node layout.** The mockup draws N3 on the **right** side, and any function can go on any compatible node.
  The device model puts N3 (ball pocket) on the **left** and fixes N1 = owner Yes button, N2 = calm audio,
  N4 = strap, N5 = spout. Use `GET /layout` as the source of truth and update `SLOTS` in `src/data.js`.
- **Function names.** Mockup functions (`play`, `outside`, `food`, `walk`, `music`, `rest`, `attention`) should be
  mapped to the device-model features (`tug`, `walk`, `choice`, `roll`, …).
- **Bark activation** is on in the mockup so there's data to show. PRD §9.5 says barking shouldn't trigger
  anything unless the owner turns it on, so default it to off in production.

## Design

- Colours, fonts and all component styles: `src/styles.css` (cream `#f6f1e7`, sage `#56704f`, ochre `#d6a043`;
  Fraunces for headings, DM Sans for body, Caveat for the diary handwriting).
- Charts: single-hue sequential sage heatmap; single-series bar charts (the brand sage/ochre pair failed a
  colourblind-safety check when shown together, so the two series are separate charts).
- `docs/`: the PRD, the handwritten feature list and the storyboard renders.
