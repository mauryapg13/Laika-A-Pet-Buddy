"""OpenCV pass over camera footage: sample snapshots, track the dog, label behaviour, cut into episodes.

Approach (no model downloads, runs on a laptop CPU):
  1. Grab frames at `sample_fps` (the rest are skipped with grab(), which is cheap).
  2. MOG2 background subtraction; the largest foreground blob is the dog.
  3. Per snapshot: position, speed, in-box motion, and which zone the dog's feet are in.
  4. Rule-based label per snapshot -> majority-vote smoothing -> run-length episodes.
  5. One keyframe per episode is saved so Claude can look at a handful of images, not the whole video.
"""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path

import cv2
import numpy as np

from .config import VisionConfig
from .detector import DogDetector, drop_person_lookalikes, mask_out_people

STATE_EMOJI = {
    "sleeping": "💤", "resting": "🛋️", "wandering": "🐾", "zoomies": "⚡", "playing": "🎾",
    "tugging": "🪢", "eating": "🍖", "waiting_at_door": "🚪", "away": "👻",
}


@dataclass
class Snapshot:
    t: float
    frame_idx: int
    present: bool
    bbox: tuple | None          # normalized x1, y1, x2, y2
    feet: tuple | None          # normalized bottom-centre of the box
    speed: float                # body lengths per second
    motion: float               # fraction of the dog's box that changed since last snapshot
    zone: str | None
    label: str = ""
    n_dogs: int = 0             # dogs the detector saw (0 when running on motion only)
    n_people: int = 0           # people in view (the owner coming by), from the detector
    body_px: float = 0.0        # dog's size (longest box side, working-frame pixels), the unit for speed


@dataclass
class Episode:
    id: int
    state: str
    zone: str | None
    start_s: float
    end_s: float
    peak_speed: float
    mean_motion: float
    keyframe_idx: int
    keyframe_path: str | None = None
    caption: str | None = None  # filled in later by Claude vision, if enabled

    @property
    def duration_s(self) -> float:
        return self.end_s - self.start_s


@dataclass
class VisionResult:
    video: str
    fps: float
    duration_s: float
    snapshots: list[Snapshot]
    episodes: list[Episode]
    stats: dict = field(default_factory=dict)
    human_visits: list = field(default_factory=list)  # [(start_s, end_s)] when a person was in view

    def to_dict(self) -> dict:
        return {
            "video": self.video,
            "fps": self.fps,
            "duration_s": round(self.duration_s, 1),
            "stats": self.stats,
            "human_visits": self.human_visits,
            "episodes": [asdict(e) | {"duration_s": round(e.duration_s, 1)} for e in self.episodes],
        }


def _zone_of(point, zones) -> str | None:
    if point is None:
        return None
    x, y = point
    for name, (x1, y1, x2, y2) in zones.items():
        if x1 <= x <= x2 and y1 <= y <= y2:
            return name
    return None


def _classify(s: Snapshot, cfg: VisionConfig, gone: bool, net_speed: float, path_speed: float) -> str:
    """net_speed: how far the dog actually got over ~2 s. path_speed: how much it moved to get there."""
    if gone:
        return "away"
    if path_speed >= cfg.zoomies_speed:
        return "zoomies"
    if net_speed < cfg.walking_speed and s.zone == "food_bowl" and s.motion > cfg.still_motion:
        return "eating"  # head-down busy at the bowl looks like play to the motion numbers
    if net_speed < cfg.walking_speed and (s.motion >= cfg.active_motion or s.speed >= cfg.walking_speed):
        # Busy but not going anywhere.
        return "tugging" if s.zone == "tug_device" else "playing"
    if net_speed >= cfg.walking_speed:
        return "wandering"
    # Note: MOG2 absorbs a dog that stays in one spot, so s.present can be False here; position then comes
    # from the last sighting and s.motion (frame differencing) still tells still from busy.
    if s.zone == "food_bowl" and s.motion > cfg.still_motion:
        return "eating"
    if s.zone == "door":
        return "waiting_at_door"
    return "resting"


def _find_dog(contours, w, h, cfg: VisionConfig):
    """Pick the dog out of the foreground blobs. A real dog often splits into pieces (head, body, tail)
    and comes with noise (curtain edges, a nudged bowl), so: drop slivers, take the biggest blob, and
    union in the sizeable blobs close to it."""
    boxes = []
    for c in contours:
        a = cv2.contourArea(c)
        x, y, bw, bh = cv2.boundingRect(c)
        if a < 0.2 * cfg.min_blob_frac * w * h or not (0.15 <= bw / bh <= 7):
            continue
        boxes.append((a, x, y, x + bw, y + bh))
    if not boxes:
        return None, 0.0
    boxes.sort(reverse=True)
    main_area, x1, y1, x2, y2 = boxes[0]
    reach = 0.12 * max(w, h)
    total = main_area
    for a, bx1, by1, bx2, by2 in boxes[1:]:
        gap = max(bx1 - x2, x1 - bx2, by1 - y2, y1 - by2, 0)
        if a >= 0.1 * main_area and gap <= reach:
            x1, y1, x2, y2 = min(x1, bx1), min(y1, by1), max(x2, bx2), max(y2, by2)
            total += a
    return (x1, y1, x2, y2), total / (w * h)


def _smooth(labels: list[str], window: int) -> list[str]:
    half = window // 2
    out = []
    for i in range(len(labels)):
        votes = Counter(labels[max(0, i - half): i + half + 1])
        out.append(votes.most_common(1)[0][0])
    return out


def _episodes(snaps: list[Snapshot], cfg: VisionConfig, dt: float) -> list[Episode]:
    runs: list[list[Snapshot]] = []
    for s in snaps:
        if runs and runs[-1][0].label == s.label:
            runs[-1].append(s)
        else:
            runs.append([s])

    # Fold runs that are too short into the previous run (or the next one, at the very start).
    merged: list[list[Snapshot]] = []
    for run in runs:
        if merged and len(run) * dt < cfg.min_episode_s:
            merged[-1].extend(run)
        elif merged and merged[-1][0].label == run[0].label:
            merged[-1].extend(run)
        else:
            merged.append(run)
    if len(merged) > 1 and len(merged[0]) * dt < cfg.min_episode_s:
        merged[1] = merged[0] + merged[1]
        merged.pop(0)

    episodes = []
    for run in merged:
        state = Counter(s.label for s in run).most_common(1)[0][0]
        # Long stretches of resting become sleeping.
        if state == "resting" and len(run) * dt >= cfg.sleep_after_s:
            state = "sleeping"
        zones = [s.zone for s in run if s.zone]
        zone = Counter(zones).most_common(1)[0][0] if zones else None
        active = state in ("zoomies", "playing", "tugging", "wandering", "eating")
        key = max(run, key=lambda s: s.motion) if active else run[len(run) // 2]
        episodes.append(Episode(
            id=len(episodes), state=state, zone=zone,
            start_s=run[0].t, end_s=run[-1].t + dt,
            peak_speed=round(max(s.speed for s in run), 3),
            mean_motion=round(float(np.mean([s.motion for s in run])), 3),
            keyframe_idx=key.frame_idx,
        ))
    return episodes


def _human_visits(snaps: list[Snapshot], dt: float, min_s: float = 2.0) -> list[tuple[float, float]]:
    """Stretches where a person was in view, bridging gaps under 5 s (people walk behind furniture)."""
    visits = []
    for s in snaps:
        if s.n_people:
            if visits and s.t - visits[-1][1] <= 5:
                visits[-1][1] = s.t + dt
            else:
                visits.append([s.t, s.t + dt])
    return [(round(a, 1), round(b, 1)) for a, b in visits if b - a >= min_s]


def _stats(snaps: list[Snapshot], episodes: list[Episode], dt: float) -> dict:
    time_in_state = Counter()
    for e in episodes:
        time_in_state[e.state] += e.duration_s
    zone_visits = Counter(e.zone for e in episodes if e.zone)
    distance = 0.0
    prev = None
    for s in snaps:
        if s.feet and prev:
            distance += math.dist(s.feet, prev)
        prev = s.feet if s.feet else prev
    return {
        "seconds_by_state": {k: round(v, 1) for k, v in time_in_state.most_common()},
        "episodes_by_state": dict(Counter(e.state for e in episodes)),
        "zone_visits": dict(zone_visits),
        "zoomies_bursts": sum(1 for e in episodes if e.state == "zoomies"),
        "longest_nap_s": round(max((e.duration_s for e in episodes if e.state == "sleeping"), default=0), 1),
        # Distance in "room widths" (the frame width), a fun unit for the report.
        "distance_room_widths": round(distance, 1),
        "top_speed_body_lengths_per_s": round(max((s.speed for s in snaps), default=0), 3),
        "most_dogs_in_frame": max((s.n_dogs for s in snaps), default=0),
    }


def _shrink(frame, width):
    h, w = frame.shape[:2]
    return cv2.resize(frame, (width, int(h * width / w)))


def _draw(frame, s: Snapshot, cfg: VisionConfig):
    h, w = frame.shape[:2]
    for name, (x1, y1, x2, y2) in cfg.zones.items():
        cv2.rectangle(frame, (int(x1 * w), int(y1 * h)), (int(x2 * w), int(y2 * h)), (200, 200, 200), 1)
        cv2.putText(frame, name, (int(x1 * w) + 3, int(y1 * h) + 14), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
    if s.bbox:
        x1, y1, x2, y2 = s.bbox
        cv2.rectangle(frame, (int(x1 * w), int(y1 * h)), (int(x2 * w), int(y2 * h)), (0, 220, 255), 2)
    cv2.putText(frame, f"{s.t:6.1f}s  {s.label}  v={s.speed:.2f} m={s.motion:.2f}",
                (8, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    return frame


def analyze_video(path: str | Path, out_dir: str | Path, cfg: VisionConfig | None = None,
                  debug_video: bool = False) -> VisionResult:
    cfg = cfg or VisionConfig()
    path, out_dir = Path(path), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise FileNotFoundError(f"Could not open video: {path}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    step = max(1, round(fps / cfg.sample_fps))
    dt = step / fps

    bg = cv2.createBackgroundSubtractorMOG2(history=int(60 * cfg.sample_fps), varThreshold=32, detectShadows=True)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    snaps: list[Snapshot] = []
    gone_flags: list[bool] = []
    prev_gray = None
    last_seen_t = -1e9
    last_bbox = last_feet = None
    last_speed = 0.0
    gone, gone_since = True, 0  # "gone" until the dog first shows up
    seen_leaving = False         # True once we have evidence it left (vs. never seen yet)
    # "Empty room" reference, learned only from pixels away from the dog. Lets us tell a dog that went
    # still (absorbed by MOG2, but its spot still differs from the empty room) from one that slipped out.
    empty_bg = known = None
    empty_checks = 0
    frame_idx = 0
    detector = DogDetector() if cfg.use_detector and DogDetector.available() else None
    body_px = 0.0
    detector_works = False  # stays False on footage the detector can't read (e.g. the cartoon test clip)

    while True:
        if frame_idx % step:
            if not cap.grab():
                break
            frame_idx += 1
            continue
        ok, frame = cap.read()
        if not ok:
            break
        t = frame_idx / fps
        small = _shrink(frame, cfg.work_width)
        h, w = small.shape[:2]
        gray = cv2.GaussianBlur(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY), (7, 7), 0)

        mask = bg.apply(small, learningRate=1.0 if not snaps else -1)
        mask = cv2.threshold(mask, 200, 255, cv2.THRESH_BINARY)[1]  # drop shadow pixels (value 127)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        dets, people = detector.detect(frame) if detector else ([], [])
        dets = drop_person_lookalikes(dets, people)
        mask_out_people(mask, people)  # a walking human must never become "the dog"
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        dog_rect, area = _find_dog(contours, w, h, cfg)
        # Ignore tiny noise and huge blobs (lights switching on, camera auto-exposure).
        present = dog_rect is not None and cfg.min_blob_frac <= area <= 0.6

        if dets:
            detector_works = True
            # Several dogs: follow the one nearest to where "our" dog was.
            ref = last_feet or (0.5, 1.0)
            x1, y1, x2, y2, _ = min(dets, key=lambda d: math.dist(((d[0] + d[2]) / 2, d[3]), ref))
            dog_rect, present = (int(x1 * w), int(y1 * h), int(x2 * w), int(y2 * h)), True
        elif detector_works:
            # The detector sees dogs in this footage but not now. Leftover motion blobs are shadows or a
            # nudged bowl; the still-dog / left-the-room logic below decides whether it's there.
            present = False

        if empty_bg is None:
            empty_bg, known = small.astype(np.float32), np.zeros(gray.shape, bool)
        dog_box = None
        if present:
            dog_box = dog_rect
        elif not gone and last_bbox:
            dog_box = (int(last_bbox[0] * w), int(last_bbox[1] * h), int(last_bbox[2] * w), int(last_bbox[3] * h))
        if not gone or present:
            away_from_dog = np.ones(gray.shape, np.uint8)
            if dog_box:
                x1, y1, x2, y2 = dog_box
                pad = 12
                away_from_dog[max(0, y1 - pad):y2 + pad, max(0, x1 - pad):x2 + pad] = 0
            cv2.accumulateWeighted(small.astype(np.float32), empty_bg, 0.1, mask=away_from_dog)
            known |= away_from_dog.astype(bool)

        bbox = feet = None
        speed = 0.0
        if not present and not gone and last_bbox and dog_box:
            x1, y1, x2, y2 = dog_box
            region_known = known[y1:y2, x1:x2]
            if region_known.size and region_known.mean() > 0.8:
                # Colour, not grey: a brown dog and a brown door can have the same brightness.
                differs = np.abs(small[y1:y2, x1:x2].astype(np.float32) - empty_bg[y1:y2, x1:x2]).max(axis=2) > 25
                empty_checks = empty_checks + 1 if differs.mean() < 0.08 else 0
                if empty_checks >= 3:  # its spot looks like the empty room for 3 snapshots: it left
                    gone, gone_since, seen_leaving = True, len(snaps) - 2, True
                    for j in range(gone_since, len(snaps)):
                        gone_flags[j] = True
        if not present and not gone and last_feet:
            # It left if it vanished at the frame edge. (Exits through a door mid-frame are caught by the
            # empty-room check above.)
            fx, fy = last_feet
            if min(fx, 1 - fx, fy, 1 - fy) < 0.06:
                gone, gone_since, seen_leaving = True, len(snaps), True
        if present:
            empty_checks = 0
            x, y, x2, y2 = dog_rect
            bw, bh = x2 - x, y2 - y
            bbox = (x / w, y / h, (x + bw) / w, (y + bh) / h)
            feet = ((x + bw / 2) / w, (y + bh) / h)
            if gone and not seen_leaving and min(feet[0], 1 - feet[0], feet[1], 1 - feet[1]) > 0.1:
                # It "appeared" mid-room, not at an edge: it was lying there all along and the background
                # model had absorbed it. Backfill that stretch as the dog resting at this spot.
                for j in range(gone_since, len(snaps)):
                    snaps[j].feet = feet
                    gone_flags[j] = False
            body_px = max(bw, bh) if not body_px else 0.7 * body_px + 0.3 * max(bw, bh)
            if last_feet and t - last_seen_t < 3:
                # Body lengths per second: the same trot is "fast" whether the dog is near or far from the lens.
                moved_px = math.hypot((feet[0] - last_feet[0]) * w, (feet[1] - last_feet[1]) * h)
                speed = moved_px / body_px / (t - last_seen_t)
            gone = False
            last_seen_t, last_bbox, last_feet, last_speed = t, bbox, feet, speed

        # In-box motion from plain frame differencing: catches tugging/chewing where the dog doesn't travel.
        motion = 0.0
        box = bbox or (None if gone else last_bbox)
        if prev_gray is not None and box:
            x1, y1, x2, y2 = int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h)
            diff = cv2.absdiff(gray[y1:y2, x1:x2], prev_gray[y1:y2, x1:x2])
            if diff.size:
                motion = float((diff > 25).mean())
        prev_gray = gray

        snaps.append(Snapshot(t=round(t, 2), frame_idx=frame_idx, present=present, bbox=bbox,
                              feet=feet or (None if gone else last_feet),
                              speed=round(speed, 3), motion=round(motion, 3), zone=None, n_dogs=len(dets), n_people=len(people),
                              body_px=round(body_px, 1)))
        gone_flags.append(gone)
        frame_idx += 1

    if not snaps:
        raise ValueError(f"No frames could be read from {path}")

    # Net travel over a ~2 s window separates walking (gets somewhere) from tugging (lots of jiggle, no travel).
    k = max(1, round(cfg.sample_fps))
    for i, s in enumerate(snaps):
        s.zone = _zone_of(s.feet, cfg.zones)
        a, b = snaps[max(0, i - k)], snaps[min(len(snaps) - 1, i + k)]
        net = 0.0
        if a.feet and b.feet and b.t > a.t and s.body_px:
            net = math.hypot((b.feet[0] - a.feet[0]) * w, (b.feet[1] - a.feet[1]) * h) / s.body_px / (b.t - a.t)
        path = float(np.mean([x.speed for x in snaps[max(0, i - k): i + k + 1]]))
        s.label = _classify(s, cfg, gone_flags[i], net, path)

    for s, lab in zip(snaps, _smooth([s.label for s in snaps], cfg.smooth_window)):
        s.label = lab
    episodes = _episodes(snaps, cfg, dt)

    if debug_video:
        writer = None
        for s in snaps:
            cap.set(cv2.CAP_PROP_POS_FRAMES, s.frame_idx)
            ok, frame = cap.read()
            if not ok:
                break
            small = _shrink(frame, cfg.work_width)
            if writer is None:
                writer = cv2.VideoWriter(str(out_dir / "debug_tracking.mp4"), cv2.VideoWriter_fourcc(*"mp4v"),
                                         cfg.sample_fps * 2, small.shape[1::-1])
            writer.write(_draw(small, s, cfg))
        if writer:
            writer.release()

    # Save one keyframe per episode (seek back into the video instead of holding frames in memory).
    kf_dir = out_dir / "keyframes"
    kf_dir.mkdir(parents=True, exist_ok=True)
    for old in kf_dir.glob("ep*.jpg"):  # keyframes from a previous run of this output folder
        old.unlink()
    for e in episodes:
        cap.set(cv2.CAP_PROP_POS_FRAMES, e.keyframe_idx)
        ok, frame = cap.read()
        if ok:
            frame = _shrink(frame, 640)
            p = kf_dir / f"ep{e.id:03d}_{e.state}.jpg"
            cv2.imwrite(str(p), frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            e.keyframe_path = str(p)
    cap.release()

    duration = total / fps if total else snaps[-1].t + dt
    # Only trust "no people seen" when the detector demonstrably works on this footage (it found the dog).
    visits = _human_visits(snaps, dt) if detector_works else None
    stats = _stats(snaps, episodes, dt)
    stats["humans_detectable"] = detector_works
    stats["human_seen_s"] = round(sum(e - s for s, e in visits), 1) if visits is not None else None
    return VisionResult(video=str(path), fps=fps, duration_s=duration, snapshots=snaps,
                        episodes=episodes, stats=stats, human_visits=visits or [])
