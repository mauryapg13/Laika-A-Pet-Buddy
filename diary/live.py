"""Live demo: webcam -> behaviour tracking + the Laika hub -> a diary that writes itself as things happen.

    python -m diary.live --name Pablo              # laptop camera
    python -m diary.live --source data/videos/x.mp4  # replay a file at real speed (loops)

Open http://localhost:8765. A real device_model.Hub runs in-process: the camera feeds it HUMAN_DETECTED
(which triggers Laika's greeting) and the dog's activity; the page's buttons stand in for the hub's
physical buttons and sensors. "End of day" writes the whole-day diary, the real product deliverable.
"""
from __future__ import annotations

import argparse
import html
import json
import math
import sys
import threading
import time
from collections import Counter, deque
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import anthropic
import cv2
import numpy as np

from camera.config import VisionConfig
from camera.detector import DogDetector, drop_person_lookalikes, mask_out_people
from camera.vision import STATE_EMOJI, Snapshot, _classify, _draw, _find_dog, _shrink, _zone_of
from device_model import Hub

from .env import load_dotenv
from .hub_events import HUB_CONTEXT, drive, moment_for
from .claude import (FALLBACK_BETA, _client, _model, _part_of_day, _text, credentials_available,
                     write_diary)

# What the dog "says" happened when a behaviour starts.
LIVE_PHRASES = {
    "sleeping": "fell asleep", "resting": "lay down and rested", "wandering": "walked around the room",
    "zoomies": "got the zoomies and ran around fast", "playing": "started playing",
    "tugging": "started tugging at the hub", "eating": "went to my food bowl",
    "waiting_at_door": "sat by the door and waited", "away": "left the room",
}


class LiveTracker:
    """The batch tracker's rules, run causally one snapshot at a time."""

    def __init__(self, cfg: VisionConfig, detector: DogDetector | None, track_anything: bool = False):
        self.cfg, self.detector = cfg, detector
        # Without a detector there's nothing to tell a dog from a person, so motion is all we have.
        self.track_anything = track_anything or detector is None
        self.bg = cv2.createBackgroundSubtractorMOG2(history=int(30 * cfg.sample_fps), varThreshold=32,
                                                     detectShadows=True)
        self.kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        self.window = deque(maxlen=max(3, round(cfg.sample_fps * 2)))   # ~2 s, for net/path speed
        self.labels = deque(maxlen=cfg.smooth_window)
        self.prev_gray = None
        self.last_feet = self.last_box = None
        self.last_seen_t = -1e9
        self.body_px = 0.0
        self.still_since = None
        self.people_votes = deque(maxlen=round(cfg.sample_fps * 7))  # ~7 s of memory
        self.people_conf = 0.0
        self.human_here = False

    def step(self, frame, t: float) -> tuple[Snapshot, bool]:
        cfg = self.cfg
        small = _shrink(frame, cfg.work_width)
        h, w = small.shape[:2]
        gray = cv2.GaussianBlur(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY), (7, 7), 0)
        mask = self.bg.apply(small)
        mask = cv2.threshold(mask, 200, 255, cv2.THRESH_BINARY)[1]
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self.kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, self.kernel, iterations=2)
        dogs, people = self.detector.detect(frame) if self.detector else ([], [])
        dogs = drop_person_lookalikes(dogs, people)
        if people:
            self.people_conf = max(p[4] for p in people)
        if not self.track_anything:
            mask_out_people(mask, people)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        rect, area = _find_dog(contours, w, h, cfg)
        present = rect is not None and cfg.min_blob_frac <= area <= 0.6

        if dogs:
            ref = self.last_feet or (0.5, 1.0)
            x1, y1, x2, y2, _ = min(dogs, key=lambda d: math.dist(((d[0] + d[2]) / 2, d[3]), ref))
            rect, present = (int(x1 * w), int(y1 * h), int(x2 * w), int(y2 * h)), True
        elif not self.track_anything:
            # Only a detected dog counts. Leftover motion is people, shadows, a chair moving.
            present = False

        bbox = feet = None
        speed = 0.0
        if present:
            x1, y1, x2, y2 = rect
            bbox = (x1 / w, y1 / h, x2 / w, y2 / h)
            feet = ((x1 + x2) / 2 / w, y2 / h)
            side = max(x2 - x1, y2 - y1)
            self.body_px = side if not self.body_px else 0.7 * self.body_px + 0.3 * side
            if self.last_feet and t - self.last_seen_t < 3:
                moved = math.hypot((feet[0] - self.last_feet[0]) * w, (feet[1] - self.last_feet[1]) * h)
                speed = moved / self.body_px / (t - self.last_seen_t)
            self.last_feet, self.last_box, self.last_seen_t = feet, bbox, t
        gone = not present and t - self.last_seen_t > 8

        motion = 0.0
        box = bbox or (None if gone else self.last_box)
        if self.prev_gray is not None and box:
            bx1, by1, bx2, by2 = int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h)
            diff = cv2.absdiff(gray[by1:by2, bx1:bx2], self.prev_gray[by1:by2, bx1:bx2])
            if diff.size:
                motion = float((diff > 25).mean())
        self.prev_gray = gray

        s = Snapshot(t=round(t, 2), frame_idx=0, present=present, bbox=bbox,
                     feet=feet or (None if gone else self.last_feet), speed=round(speed, 3),
                     motion=round(motion, 3), zone=None, n_dogs=len(dogs), n_people=len(people),
                     body_px=round(self.body_px, 1))
        s.zone = _zone_of(s.feet, cfg.zones)
        self.window.append(s)
        a, b = self.window[0], self.window[-1]
        net = 0.0
        if a.feet and b.feet and b.t > a.t and self.body_px:
            net = math.hypot((b.feet[0] - a.feet[0]) * w, (b.feet[1] - a.feet[1]) * h) / self.body_px / (b.t - a.t)
        path = float(np.mean([x.speed for x in self.window]))
        label = _classify(s, cfg, gone, net, path)
        if label == "resting":
            self.still_since = self.still_since or t
            if t - self.still_since >= cfg.sleep_after_s:
                label = "sleeping"
        else:
            self.still_since = None
        self.labels.append(label)
        s.label = Counter(self.labels).most_common(1)[0][0]

        # People only count as "my human" when the subject is a real dog (in a no-dog demo the person IS the dog).
        # Hysteresis: arrive after ~1 s of sightings, leave only after ~7 s unseen (people walk behind things).
        # In track-anything mode the moving person is standing in for the dog, so they aren't "my human".
        self.people_votes.append(bool(people) and not self.track_anything)
        recent = list(self.people_votes)[-round(self.cfg.sample_fps):]
        if not self.human_here and len(recent) >= 2 and all(recent):
            self.human_here = True
        elif self.human_here and len(self.people_votes) == self.people_votes.maxlen and not any(self.people_votes):
            self.human_here = False
        return s, self.human_here


LIVE_SYSTEM = """You are writing a dog's diary live, while the day is happening, in the dog's own voice.

You get the diary so far and the NEW MOMENTS that just happened. Write only the next bit: 1-3 short
sentences about the new moments, feelings first (happy, proud, bored, hopeful, cozy, lonely, grumpy),
simple, sweet and gently funny. It must read as a natural continuation, so don't repeat what the diary
already says and don't greet, date or sign off.

Strict: only the new moments happened. Never add an action, place, object or person that isn't in them.
Feelings and dog logic about them are yours. No numbers, no clock times, never mention cameras or data.

For context only (the dog just calls it "the hub" or "Laika"): """ + HUB_CONTEXT


class LiveDiary:
    def __init__(self, dog: dict, use_claude: bool, min_gap_s: float = 12):
        self.dog, self.use_claude, self.min_gap_s = dog, use_claude, min_gap_s
        self.entries: list[dict] = []       # {"time", "text"}
        self.moments: list[dict] = []       # everything that happened, for the end-of-day diary
        self.pending: list[dict] = []
        self.final: str | None = None
        self.lock = threading.Lock()
        self.last_call = 0.0
        threading.Thread(target=self._writer, daemon=True).start()

    def add(self, text: str):
        now = datetime.now().strftime("%H:%M")
        m = {"clock": now, "when": _part_of_day(now), "moment": text}
        with self.lock:
            self.moments.append(m)
            self.pending.append(m)

    def _writer(self):
        while True:
            time.sleep(1)
            with self.lock:
                if not self.pending or time.time() - self.last_call < self.min_gap_s:
                    continue
                batch, self.pending = self.pending, []
                so_far = " ".join(e["text"] for e in self.entries[-8:])
            self.last_call = time.time()
            text = None
            if self.use_claude:
                try:
                    response = _client().beta.messages.create(
                        model=_model(), max_tokens=2000, betas=[FALLBACK_BETA], fallbacks="default",
                        output_config={"effort": "low"}, system=LIVE_SYSTEM,
                        messages=[{"role": "user", "content": json.dumps({
                            "dog": self.dog, "diary_so_far": so_far or "(nothing yet, this is the first line)",
                            "new_moments": [m["moment"] for m in batch]})}])
                    text = _text(response).strip()
                except (anthropic.APIError, RuntimeError) as e:
                    print(f"diary call failed: {e}", file=sys.stderr)
            if not text:  # never stall the demo
                text = " ".join(f"I {m['moment']}." for m in batch)
            with self.lock:
                self.entries.append({"time": batch[-1]["clock"], "text": text})

    def finish(self, date: str) -> str:
        with self.lock:
            moments = []
            for m in self.moments:  # merge back-to-back repeats, like the batch pipeline
                if moments and moments[-1]["moment"] == m["moment"]:
                    moments[-1]["times"] = moments[-1].get("times", 1) + 1
                else:
                    moments.append({"when": m["when"], "moment": m["moment"]})
            for i, m in enumerate(moments, 1):
                m["id"] = i
        if not moments:
            text = "*Nothing happened yet.*"
        elif self.use_claude:
            try:
                text, _ = write_diary(self.dog, date, moments)
            except (anthropic.APIError, RuntimeError, ValueError) as e:
                text = f"*Couldn't write the summary: {e}*"
        else:
            text = "\n\n".join(e["text"] for e in self.entries) + f"\n\n{self.dog['name']} 🐾"
        with self.lock:
            self.final = text
        return text


def saved_diaries(out_dir: str | Path) -> dict[str, dict]:
    """Diaries already written to out/, newest per day: {"YYYY-MM-DD": {"text", "folder"}}."""
    found: dict[str, dict] = {}
    for f in sorted(Path(out_dir).glob("*/diary.md"), key=lambda f: f.stat().st_mtime):
        name = f.parent.name
        day = name[5:15] if name.startswith("live_") else name[:10]
        if len(day) == 10 and day[4] == "-" and day[7] == "-":
            found[day] = {"text": f.read_text(), "folder": name}
    return found


class App:
    def __init__(self, args):
        self.args = args
        self.cfg = VisionConfig(sample_fps=args.sample_fps, sleep_after_s=args.sleep_after, min_episode_s=4)
        self.cfg.zones = {k: tuple(v) for k, v in json.loads(Path(args.zones).read_text()).items()} if args.zones else {}
        self.detector = DogDetector() if DogDetector.available() else None
        self.tracker = LiveTracker(self.cfg, self.detector, track_anything=args.track_anything)
        self.hub = Hub()                    # the real Laika device model, in-process
        self.hub_lock = threading.Lock()
        self.hub_out: dict = self.hub.handle({"type": "tick"})
        self.gesture = {"ears": "neutral", "halo": "off", "until": 0.0}  # hold a gesture on screen for a moment
        self.notifications: list[str] = []
        self.dog = {"name": args.name, "breed": args.breed}
        self.diary = LiveDiary(self.dog, use_claude=credentials_available() and not args.offline)
        self.jpeg = None
        self.snap: Snapshot | None = None
        self.state, self.cand, self.cand_since = None, None, 0.0
        self.human = False
        self.lock = threading.Lock()
        threading.Thread(target=self._tick_loop, daemon=True).start()

    # ---- hub
    def send(self, msg: dict) -> dict:
        """One input to the hub (auto-confirming any output like the sensor would); hub events become moments."""
        with self.hub_lock:
            outs = drive(self.hub, msg, sensor_delay_s=0)
            for out in outs:
                for e in out["events"]:
                    m = moment_for(e)
                    if m:
                        self.diary.add(m)
                self.notifications = (self.notifications + out["notifications"])[-20:]
                if out["ears"] != "neutral" or out["halo"] != "off":
                    self.gesture = {"ears": out["ears"], "halo": out["halo"], "until": time.time() + 4}
            self.hub_out = outs[-1]
        return outs[-1]

    def _tick_loop(self):
        while True:  # timers: session timeouts, request expiry, lockout end
            time.sleep(1)
            self.send({"type": "tick"})

    # ---- camera
    def _on_label(self, label: str, t: float):
        """Report a behaviour once it has held for min_episode_s, so flicker doesn't become diary lines."""
        if label == self.state:
            self.cand = None
            return
        if label != self.cand:
            self.cand, self.cand_since = label, t
            return
        if t - self.cand_since >= self.cfg.min_episode_s:
            was_away, first = self.state == "away", self.state is None
            self.state, self.cand = label, None
            if first and label == "away":
                return  # no dog yet at startup: nothing happened
            self.diary.add("came into the room" if first else
                           "came back into the room" if was_away and label != "away" else LIVE_PHRASES[label])
            # The hub's camera channel keeps the activity label (it shows up in GET /summary -> camera).
            self.send({"type": "camera", "event": f"DOG_{label.upper()}", "confidence": 0.8})

    def _on_human(self, here: bool):
        if not here:
            self.diary.add("my human left the room")
            return
        out = self.send({"type": "camera", "event": "HUMAN_DETECTED",
                         "confidence": round(self.tracker.people_conf, 2)})
        if not any(e["event"] == "GREETING" for e in out["events"]):
            self.diary.add("my human came into the room")  # (a greeting already made its own moment)

    def capture_loop(self):
        src = int(self.args.source) if self.args.source.isdigit() else self.args.source
        cap = cv2.VideoCapture(src)
        if not cap.isOpened():
            sys.exit(f"Could not open camera/source {self.args.source!r}. On macOS, allow camera access for your "
                     f"terminal app in System Settings > Privacy & Security > Camera, then retry.")
        is_file = not isinstance(src, int)
        file_fps = cap.get(cv2.CAP_PROP_FPS) or 30
        t0, last_sample = time.time(), 0.0
        while True:
            ok, frame = cap.read()
            if not ok:
                if is_file:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                time.sleep(0.05)
                continue
            if is_file:
                time.sleep(1 / file_fps)  # replay at real speed
            t = time.time() - t0
            if t - last_sample >= 1 / self.cfg.sample_fps:
                last_sample = t
                snap, human = self.tracker.step(frame, t)
                self._on_label(snap.label, t)
                if human != self.human:
                    self.human = human
                    self._on_human(human)
                with self.lock:
                    self.snap = snap
            with self.lock:
                snap = self.snap
            view = _shrink(frame, 720)
            if snap:
                view = _draw(view, snap, self.cfg)
            ok, buf = cv2.imencode(".jpg", view, [cv2.IMWRITE_JPEG_QUALITY, 75])
            if ok:
                with self.lock:
                    self.jpeg = buf.tobytes()

    def finish_day(self) -> Path:
        """Write the whole-day diary and save it with the hub's log. Returns the folder."""
        text = self.diary.finish(datetime.now().strftime("%Y-%m-%d"))
        out = Path(self.args.out) / f"live_{datetime.now():%Y-%m-%d_%H%M}_{self.dog['name'].lower()}"
        out.mkdir(parents=True, exist_ok=True)
        (out / "diary.md").write_text(text)
        with self.hub_lock:
            hub_events, summary = list(self.hub.events), self.hub.summary()
        with self.diary.lock:
            entries, moments = list(self.diary.entries), list(self.diary.moments)
        (out / "live_entries.json").write_text(json.dumps({"entries": entries, "moments": moments}, indent=1))
        (out / "hub_events.json").write_text(json.dumps(hub_events, indent=1))
        (out / "hub_summary.json").write_text(json.dumps(summary, indent=1))
        print(f"End-of-day diary saved to {out}/")
        return out

    def state_json(self) -> dict:
        with self.lock:
            snap = self.snap
        with self.diary.lock:
            entries, final = list(self.diary.entries), self.diary.final
            pending, n_moments = len(self.diary.pending), len(self.diary.moments)
        with self.hub_lock:
            h = self.hub_out
            g = self.gesture if time.time() < self.gesture["until"] else {"ears": "neutral", "halo": "off"}
            hub = {"mode": h["mode"], "device_state": h["device_state"], "strap": h["nodes"]["N4"]["state"],
                   "n1": h["nodes"]["N1"]["state"], "ears": g["ears"], "halo": g["halo"],
                   "treats": h["counters"]["treats_today"], "treats_limit": h["counters"]["treats_limit_day"],
                   "reps": h["counters"]["tug_reps"], "notifications": list(self.notifications),
                   "counts": self.hub.summary()["counts"]}
        label = self.state or (snap.label if snap else None)
        return {"label": label, "emoji": STATE_EMOJI.get(label or "", ""), "human": self.human,
                "track_anything": self.tracker.track_anything, "entries": entries, "writing": pending > 0,
                "final": final, "moments": n_moments, "hub": hub, "claude": self.diary.use_claude,
                "dog": self.dog, "date": datetime.now().strftime("%Y-%m-%d")}


PAGE = r"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Laika · __NAME__'s Live Diary</title><style>
:root{--bg:#fffaf2;--fg:#2b2118;--muted:#7a6a58;--card:#fff;--line:#eadfce;--accent:#c0662a;--ok:#3c8d5a}
@media (prefers-color-scheme:dark){:root{--bg:#1d1813;--fg:#f3eadf;--muted:#b6a48f;--card:#2a221b;--line:#3d3228;--accent:#f0a24a;--ok:#6cc08b}}
*{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 -apple-system,system-ui,sans-serif}
.wrap{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(0,1fr);gap:24px;max-width:1280px;margin:auto;padding:24px 16px}
@media (max-width:860px){.wrap{grid-template-columns:1fr}}
h1{font:600 1.3rem/1.2 Georgia,serif;margin:0 0 12px} h2{font-size:.8rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin:16px 0 6px}
.cam{width:100%;border-radius:10px;border:1px solid var(--line);background:#000;display:block}
.status{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}
.chip{background:var(--card);border:1px solid var(--line);border-radius:999px;padding:4px 12px}
.row{display:flex;gap:6px;flex-wrap:wrap}
button{font:inherit;font-size:.9rem;padding:6px 12px;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--fg);cursor:pointer}
button:hover{border-color:var(--accent)} .end{background:var(--accent);color:#fff;border-color:var(--accent);margin-top:14px}
.hub{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 12px;margin-top:10px}
.hub b{font-weight:600} .notes{font-size:.85rem;color:var(--muted);margin:6px 0 0;padding-left:18px}
.paper{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:28px 28px 8px;min-height:420px;
 background-image:repeating-linear-gradient(transparent 0 31px,var(--line) 31px 32px);background-position:0 12px}
.paper p{font:18px/32px Georgia,serif;margin:0 0 32px} .date{color:var(--accent);font-style:italic}
.t{font:12px/1 -apple-system,system-ui,sans-serif;color:var(--muted);margin-right:8px}
.new{animation:fade 1.2s ease} @keyframes fade{from{opacity:0;transform:translateY(4px)}to{opacity:1}}
.muted{color:var(--muted);font-size:.85rem}
</style></head><body><div class="wrap">
<section><h1>Laika · live camera</h1><img class="cam" src="/stream" alt="camera">
<div class="status"><span class="chip" id="state">Watching…</span><span class="chip" id="human"></span></div>
<div class="hub" id="hub"></div>
<h2>Owner (app)</h2><div class="row">
<button onclick="send({type:'owner',action:'offer',feature:'tug'})">Offer tug</button>
<button onclick="send({type:'owner',action:'offer',feature:'walk'})">Clip harness (walk)</button>
<button onclick="send({type:'owner',action:'offer',feature:'roll'})">Ball game</button>
<button onclick="send({type:'owner',action:'offer',feature:'choice'})">Choice ropes</button>
<button onclick="send({type:'button',node:'N1'})">N1 · Yes / tidy</button>
<button onclick="send({type:'owner',action:'park'})">Park</button></div>
<h2>Dog (hub sensors)</h2><div class="row">
<button onclick="send({type:'pull',node:'N4',force:5.5,duration_ms:800})">🦴 Pull strap</button>
<button onclick="send({type:'release',node:'N4'})">Let go</button>
<button onclick="send({type:'boop',duration_ms:300})">🐽 Boop</button>
<button onclick="send({type:'ball_in'})">🎾 Ball in pocket</button>
<button onclick="send({type:'toy_in_basket'})">🧸 Toy in basket</button>
<button onclick="send({type:'pull',node:'C_LEFT',force:4.5,duration_ms:700})">Outside</button>
<button onclick="send({type:'pull',node:'C_CENTER',force:4.5,duration_ms:700})">Rest</button>
<button onclick="send({type:'pull',node:'C_RIGHT',force:4.5,duration_ms:700})">Play</button>
<button onclick="send({type:'button',node:'N2'})">🎵 Music</button></div>
<button class="end" onclick="finish(this)">End of day ✍️</button>
<p class="muted" id="mode"></p></section>
<section><h1>__NAME__'s diary</h1><div class="paper" id="paper"><p class="date">__DATE__</p><p>Dear Diary,</p><div id="entries"></div>
<p class="muted" id="writing" hidden>✍️ writing…</p></div></section></div>
<script>
let shown=0, finalShown=false;
const esc=s=>String(s).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
async function send(m){await fetch('/hub',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(m)});tick()}
async function finish(b){b.disabled=true;b.textContent='Writing the day…';await fetch('/finish',{method:'POST'});tick()}
async function tick(){
 try{const s=await (await fetch('/state')).json(), h=s.hub;
 document.getElementById('state').textContent=s.label&&!(s.label==='away'&&!s.track_anything)?(s.emoji+' '+s.label.replaceAll('_',' ')):(s.track_anything?'Watching…':'🔍 No dog in view');
 document.getElementById('human').textContent=s.track_anything?'🐕 Tracking whatever moves':(s.human?'🧑 Human here':'🧑 No human');
 document.getElementById('hub').innerHTML='<b>Laika hub</b> · mode <b>'+esc(h.mode)+'</b> · strap <b>'+esc(h.strap)+'</b>'+
   (h.n1==='WAITING_CONFIRM'?' · <b style="color:var(--accent)">N1 waiting for Yes</b>':'')+
   ' · ears <b>'+esc(h.ears)+'</b> · halo <b>'+esc(h.halo)+'</b> · treats <b>'+h.treats+'/'+h.treats_limit+'</b>'+
   (h.mode==='tug'?' · reps <b>'+h.reps+'/6</b>':'')+(h.device_state!=='ONLINE'?' · <b style="color:#c33">'+esc(h.device_state)+'</b>':'')+
   (h.notifications.length?'<ul class="notes">'+h.notifications.slice().reverse().map(n=>'<li>'+esc(n)+'</li>').join('')+'</ul>':'');
 document.getElementById('mode').textContent=s.claude?'':'Offline mode: add ANTHROPIC_API_KEY to .env for Claude-written entries.';
 document.getElementById('writing').hidden=!s.writing||!!s.final;
 if(s.final){const b=document.querySelector('.end');b.textContent='Day saved ✓';b.disabled=true;}
 const box=document.getElementById('entries');
 if(s.final&&!finalShown){finalShown=true;
   box.innerHTML='<p class="muted">— End of day. The whole day, in one entry: —</p>'+
   s.final.split(/\n\s*\n/).map(p=>'<p class="new">'+esc(p).replace(/^\*(.*)\*$/,'<em>$1</em>')+'</p>').join('');
   document.querySelector('.date').hidden=true;document.querySelectorAll('.paper>p')[1].hidden=true;}
 if(!finalShown){for(;shown<s.entries.length;shown++){const e=s.entries[shown];
   box.insertAdjacentHTML('beforeend','<p class="new"><span class="t">'+e.time+'</span>'+esc(e.text)+'</p>');}}
 }catch(e){}
}
setInterval(tick,1000);tick();
</script></body></html>"""


def make_handler(app: App):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, code, body: bytes, ctype="application/json"):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            path = urlparse(self.path).path
            if path == "/":
                page = (PAGE.replace("__NAME__", html.escape(app.dog["name"]))
                        .replace("__DATE__", datetime.now().strftime("%A, %d %B %Y")))
                self._send(200, page.encode(), "text/html; charset=utf-8")
            elif path == "/state":
                self._send(200, json.dumps(app.state_json()).encode())
            elif path == "/stream":
                self.send_response(200)
                self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
                self.end_headers()
                try:
                    while True:
                        with app.lock:
                            jpg = app.jpeg
                        if jpg:
                            self.wfile.write(b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpg + b"\r\n")
                        time.sleep(0.08)
                except (BrokenPipeError, ConnectionResetError):
                    pass
            else:
                self._send(404, b"{}")

        def do_POST(self):
            url = urlparse(self.path)
            if url.path == "/hub":
                # Same JSON inputs as the hub API (POST /input): one object.
                length = int(self.headers.get("Content-Length", 0))
                try:
                    msg = json.loads(self.rfile.read(length) or b"{}")
                except json.JSONDecodeError:
                    return self._send(400, b'{"error":"body must be JSON"}')
                self._send(200, json.dumps(app.send(msg)).encode())
            elif url.path == "/finish":
                app.finish_day()
                self._send(200, json.dumps({"ok": True}).encode())
            else:
                self._send(404, b"{}")

    return Handler


def build_parser(prog: str = "python -m diary.live") -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog=prog, description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", default="0", help="camera index (0 = built-in) or a video file to replay")
    ap.add_argument("--name", default="Pablo")
    ap.add_argument("--breed", default="good dog of unknown origin")
    ap.add_argument("--zones", help="zones JSON for this camera view (optional)")
    ap.add_argument("--sample-fps", type=float, default=3.0)
    ap.add_argument("--sleep-after", type=float, default=30.0, help="seconds of stillness before 'sleeping'")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--out", default="out")
    ap.add_argument("--offline", action="store_true", help="no Claude calls")
    ap.add_argument("--track-anything", action="store_true",
                    help="demo without a dog: follow whatever moves (people included) as the dog")
    return ap


def main():
    ap = build_parser()
    args = ap.parse_args()
    load_dotenv()

    app = App(args)
    threading.Thread(target=app.capture_loop, daemon=True).start()
    print(f"Detector: {'on' if app.detector else 'off (motion only)'} · Claude: {'on' if app.diary.use_claude else 'off'}")
    print(f"Open http://localhost:{args.port}   (Ctrl+C to stop)")
    try:
        ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(app)).serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
