# Laika · Owner web app

Mobile-first web app for the Laika hub. On a phone it runs fullscreen; on a laptop it shows inside a phone frame.
Screens that have a back end are **live** when `python -m api.server --camera` is running (see the table
below). Everything else still runs on **mock data**.

## Run it

Requires Node 18+. Run from `web/`:

```bash
npm install
npm run dev        # http://localhost:5173 (also shows a Network URL to open on your phone)
npm run build      # production build in dist/
```

For live data, also start the back end from the repo root: `python -m api.server --camera` (port 5050). The app
finds it on the same host as the page, so a phone on the same Wi-Fi works too. Point it elsewhere with
`VITE_LAIKA_API=http://host:port` in `web/.env.local`. Without the back end, every screen shows its mock data.
The connection code is in `src/api.js`.

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

## Mock data → back end

The back end (`python -m api.server --camera`) serves the device model (`POST /input`, `GET /state`,
`GET /summary`, `GET /events`, `GET /layout`) and the camera + diary (`GET /live`, `GET /camera/stream`,
`POST /diary/finish`, `GET /diary/days`) around **one** hub.

| UI | Status | Source |
|---|---|---|
| Dashboard: "Pablo is …", online/stop state, boops / requests / treats, latest | ✅ live | `GET /live` (camera behaviour + hub counters + notifications) |
| Notifications sheet | ✅ live | hub notifications via `GET /live` |
| Diary: today | ✅ live | live entries via `GET /live`; **Finish the day** → `POST /diary/finish` |
| Diary: past days | ✅ live (saved days) | `GET /diary/days`; mock `src/diary.js` for days without a saved diary |
| Camera view: "Laika hub" tile | ✅ live | `GET /camera/stream` (MJPEG) + detected behaviour; the other cameras are mock |
| Settings → Safety: emergency stop / resume, treat dispensing, tug play | ✅ live | `POST /input` owner `stop` / `reset`, `treats_off` / `treats_on`, `park` |
| Hub drawing + node setup (Save) | mock | node model differs from the hub (see below); `localStorage` |
| Insights | mock | `src/insights.js` (could use `GET /summary`) |
| Voice tracking | mock | no bark detection in the back end yet |
| Profile, Help | mock | `src/data.js`, `localStorage` |

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
- [`../docs/`](../docs/): the PRD, the handwritten feature list (`images/web-app-feature-notes.png`) and the storyboard renders (`images/01…06`).
