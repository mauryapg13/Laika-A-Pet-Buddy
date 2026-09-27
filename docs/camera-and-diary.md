# Camera, diary and the one back end

How the camera watches the dog, how the diary is written, and how the web app, camera and hub share one
back end. For the hub itself see [hub.md](hub.md).

## 1. Camera + diary

The camera watches the dog, the hub records what the dog does with it, and at the end of the day the dog "writes"
a diary entry about it. The owner gets a separate factual report.

```
camera ──► camera/vision.py (2-3 snapshots/s)                 Laika Hub (device_model)
            YOLO dog + person detection, MOG2 motion              ▲  camera inputs: HUMAN_DETECTED → greeting,
            → behaviour episodes, keyframes, human visits ────────┘                  DOG_<BEHAVIOUR> labels
                      │                                            │ events (tug reps, treats, walk requests,
                      ▼                                            ▼  greetings, lockouts, ball rolls, tidy…)
             diary/claude.py: one timeline → numbered "moments" → Claude writes the diary (only those moments)
             diary/owner_report.py: camera + hub counters → factual report (no LLM)
```

### 1.1 Setup
```bash
pip install -r requirements.txt
# Dog/person detector (10.9 MB, AGPL-3.0). Without it, tracking falls back to motion only.
mkdir -p models && curl -L -o models/yolo11n.onnx \
    https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n.onnx
# Claude: create .env with ANTHROPIC_API_KEY=... (plus ANTHROPIC_WORKSPACE_ID=... for org-level keys).
# Optional: LAIKA_MODEL=claude-opus-5-5 (default claude-opus-5). Without a key you get plain fallback text.
```

### 1.2 Live demo (laptop camera)
```bash
python -m diary.live --name Pablo          # open http://localhost:8765
```
- A real `Hub` runs in-process. The page's **Owner** buttons (offer tug / walk / ball / choice, N1, park) and
  **Dog** buttons (pull strap, let go, boop, ball in pocket, toy in basket, choice ropes, music) send the same JSON
  as `POST /input`. A simulated sensor confirms each output, the way the hardware will.
- The camera sends `HUMAN_DETECTED` with the detector's confidence, so Laika's arrival greeting fires for real. Each
  behaviour change is logged as a camera event (`DOG_TUGGING`, `DOG_SLEEPING`…).
- Behaviour changes and hub events become diary moments. About every 12 seconds, Claude adds a short, feelings-first
  line. **End of day** writes the whole-day entry, the real product deliverable, and saves the hub event log and
  summary to `out/live_…/`.
- Only a detected dog counts as the dog. People are masked out, so a person walking past is never tracked as the
  dog. For a demo without a dog, add `--track-anything`. To rehearse without a camera, replay a clip:
  `--source data/videos/<clip>.mp4`.

### 1.3 Whole-day batch run
```bash
python -m camera.synth_video data/videos/synthetic_day.mp4           # cartoon test day with known ground truth
python -m diary data/videos/synthetic_day.mp4 --name Pablo --time-scale 280 --persona foodie
```
- Hub events come from `--hub-events events.json` (a list, e.g. saved from `GET /events`), from `--hub-url
  http://localhost:5050` (a running `python -m api.server`), or, by default, from a real `Hub` driven through a
  simulated day. That day lines up with the camera: tugging on camera becomes a tug round, waiting at the door
  becomes a walk request, and people seen become `HUMAN_DETECTED`. `--persona foodie|athlete|diva` sets the habits.
- Output goes to `out/<date>_<name>/`:
  - `diary.html` / `diary.md`: the dog's diary.
  - `report.html` / `report.md`: the owner report.
  - `diary_moments.json`: the allowed moments, plus which ones Claude used.
  - `hub_events.json`, `timeline.json`, `vision.json`, and `keyframes/`.
- `--time-scale` stretches a short clip over a day. Use `--time-scale 1` for real footage and set `--start` to when
  the recording began.

### 1.4 How the diary stays honest
- Code turns the merged timeline into a numbered list of plain moments, for example "pulled the bone tug" (×6,
  morning), "the hub gave me a treat for a good tug round", "my human came home and the hub waved its ears hello", or
  "no human came to see me". Claude only sees that list. It may skip or merge moments and add feelings, but it may
  not add events. It returns the IDs of the moments it used.
- "No human came" is only said for the stretch the camera actually watched, and only when the detector can see
  people in that footage.
- Keyframe captions (Claude vision, up to 12 per day in one call) check the tracker's labels. In the owner report
  they appear as "Photo check".

### 1.5 Camera details
- Behaviours: `sleeping` · `resting` · `wandering` · `zoomies` · `playing` · `tugging` · `eating` ·
  `waiting_at_door` · `away`. Zone-based ones (bowl, door, tug) need zones. Run
  `python -m camera.calibrate <video> 5` and put the result in `<video>.zones.json`.
- Speeds are measured in dog body lengths per second, so thresholds work for close-ups and wide shots alike. Net
  travel over about 2 s separates walking from tugging in place.
- A still dog fades into the MOG2 background, so an "empty room" reference tells a sleeping dog apart from one that
  left. A dog that is already lying down when the video starts is backfilled once it moves.
- Tested on:
  - The synthetic day: all 9 scripted segments recovered.
  - Three Pexels clips: dog at the bowl → `eating`, corgi at the door → `waiting_at_door`, two dogs with a rope toy →
    `tugging`.

## 2. Web app + one back end

The owner web app lives in [`web/`](../web/) (React + Vite, mobile-first). One back-end process serves the hub API,
the camera and the diary around the **same** hub. A button pressed in the app shows up in the diary, and the
camera's greeting shows up in the app.

```bash
# terminal 1 (repo root): hub API + camera + live diary on http://localhost:5050
python -m api.server --camera                  # add --track-anything for a demo without a dog
# terminal 2
cd web && npm install && npm run dev           # open http://localhost:5173 (or the Network URL on your phone)
```

- **Live in the app:**
  - Dashboard: "Pablo is tugging…", online/stop state, boops, requests, treats and the latest notification.
  - Notifications.
  - Diary: today's live entry plus **Finish the day**, and saved past days.
  - The "Laika hub" camera tile.
  - Settings → Safety: emergency stop/resume, treats on/off, park the strap.
- **Still mock:** node setup (its node model differs from the hub, see [`web/README.md`](../web/README.md)), Insights, Voice tracking,
  Profile and Help. Every screen falls back to its mock data when the back end is off.
- `python -m api.server` without `--camera` is the plain hub API, as before.
- The camera options are the same as `diary.live` (`--source`, `--name`, `--zones`, `--track-anything`,
  `--offline`).
- The API port is **5050**, because macOS's AirPlay Receiver holds 5000. Change it with `--api-port`, and point the
  app at it with `VITE_LAIKA_API` in `web/.env.local`.
- Without hardware, outputs (treat, ball, harness) are confirmed by a simulated sensor, so the counts behave like
  the real hub.
