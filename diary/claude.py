"""Merge camera episodes + Laika hub events into one timeline, then have Claude write the dog's diary.

Two Claude calls:
  1. caption_keyframes: a handful of episode keyframes (images) -> what the dog is actually doing.
     OpenCV knows *that* the dog moved; this tells us it was "dragging a sock onto the bed".
  2. write_diary: timeline + stats + captions -> a short, warm diary entry in the dog's voice.
The factual owner report is separate: owner_report.py.
"""
from __future__ import annotations

import base64
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

import anthropic

from camera.vision import Episode

from .hub_events import HUB_CONTEXT, hub_timeline_rows


def _model() -> str:
    return os.environ.get("LAIKA_MODEL") or os.environ.get("PAWPORT_MODEL") or "claude-opus-5"  # read at call time so .env overrides apply
# Server-side refusal fallback: a declined request is re-run on Anthropic's recommended fallback model.
FALLBACK_BETA = "server-side-fallback-2026-07-01"


def build_timeline(episodes: list[Episode], hub_events: list[dict], video_start: datetime,
                   time_scale: float = 1.0, human_visits: list | None = None) -> list[dict]:
    """`time_scale` stretches video time onto the wall clock, e.g. a 3-minute test clip standing in
    for a 14-hour day uses time_scale=280. Real 24/7 footage uses 1."""
    rows = []
    for e in episodes:
        start = video_start + timedelta(seconds=e.start_s * time_scale)
        rows.append({
            "time": start.strftime("%H:%M"), "_sort": start, "source": "camera",
            "what": e.state, "where": e.zone, "minutes": round(e.duration_s * time_scale / 60, 1),
            **({"seen": e.caption} if e.caption else {}),
        })
    for a, b in human_visits or []:
        start = video_start + timedelta(seconds=a * time_scale)
        rows.append({"time": start.strftime("%H:%M"), "_sort": start, "source": "camera",
                     "what": "human_in_room", "where": None, "minutes": round((b - a) * time_scale / 60, 1)})
    for r in hub_timeline_rows(hub_events):
        r["_sort"] = datetime.fromisoformat(r.pop("_ts"))
        rows.append(r)
    rows.sort(key=lambda r: r["_sort"])
    for r in rows:
        del r["_sort"]
    return rows


def credentials_available() -> bool:
    """API key, auth token, or an `ant auth login` profile: the sources the SDK resolves on its own."""
    return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")
                or os.environ.get("ANTHROPIC_PROFILE") or Path("~/.config/anthropic").expanduser().is_dir())


def _client() -> anthropic.Anthropic:
    # Org-level API keys (not scoped to a workspace) must name the workspace on every request.
    workspace = os.environ.get("ANTHROPIC_WORKSPACE_ID")
    headers = {"anthropic-workspace-id": workspace} if workspace else None
    return anthropic.Anthropic(max_retries=3, default_headers=headers)


def _text(response) -> str:
    if response.stop_reason == "refusal":
        raise RuntimeError("Claude declined this request (stop_reason=refusal).")
    return "".join(b.text for b in response.content if b.type == "text")


CAPTION_SCHEMA = {
    "type": "object",
    "properties": {
        "captions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "episode_id": {"type": "integer"},
                    "activity": {"type": "string", "description": "What the dog is doing, one short sentence."},
                    "objects": {"type": "array", "items": {"type": "string"}},
                    "dog_visible": {"type": "boolean"},
                },
                "required": ["episode_id", "activity", "objects", "dog_visible"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["captions"],
    "additionalProperties": False,
}


def pick_keyframes(episodes: list[Episode], max_images: int) -> list[Episode]:
    """Longest episode of each state first (variety), then the next-longest overall."""
    with_img = [e for e in episodes if e.keyframe_path and e.state != "away"]
    by_len = sorted(with_img, key=lambda e: e.duration_s, reverse=True)
    chosen, seen = [], set()
    for e in by_len:
        if e.state not in seen:
            chosen.append(e)
            seen.add(e.state)
    for e in by_len:
        if len(chosen) >= max_images:
            break
        if e not in chosen:
            chosen.append(e)
    return sorted(chosen[:max_images], key=lambda e: e.start_s)


def caption_keyframes(episodes: list[Episode], max_images: int = 12) -> None:
    picks = pick_keyframes(episodes, max_images)
    if not picks:
        return
    content = [{"type": "text", "text": (
        "These are keyframes from a home camera watching a dog. Each is labelled with the episode id and "
        "the behaviour a simple motion tracker guessed. For each, say what the dog is really doing and name "
        "notable objects (toys, shoes, the wall hub, food bowl, couch...). If the tracker label looks wrong, "
        "describe what you actually see. If no dog is visible, set dog_visible to false.")}]
    for e in picks:
        with open(e.keyframe_path, "rb") as f:
            data = base64.standard_b64encode(f.read()).decode()
        content.append({"type": "text", "text": f"Episode {e.id}: tracker says '{e.state}' near {e.zone or 'no zone'}"})
        content.append({"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": data}})

    response = _client().beta.messages.create(
        model=_model(), max_tokens=8000, betas=[FALLBACK_BETA], fallbacks="default",
        output_config={"effort": "low", "format": {"type": "json_schema", "schema": CAPTION_SCHEMA}},
        messages=[{"role": "user", "content": content}],
    )
    by_id = {e.id: e for e in episodes}
    for c in json.loads(_text(response))["captions"]:
        if c["episode_id"] in by_id:
            e = by_id[c["episode_id"]]
            e.caption = c["activity"] if c["dog_visible"] else "(no dog in frame) " + c["activity"]


def _part_of_day(hhmm: str) -> str:
    h = int(hhmm[:2])
    return ("early morning" if h < 8 else "morning" if h < 12 else "afternoon" if h < 17
            else "evening" if h < 21 else "night")


CAMERA_MOMENTS = {
    "sleeping": "had a nap", "resting": "sat around and rested", "wandering": "walked around the room",
    "zoomies": "had the zoomies, running around fast", "playing": "played", "tugging": "played tug at the hub",
    "eating": "went to my food bowl", "waiting_at_door": "sat by the door and waited",
    "away": "went out of the room", "human_in_room": "my human was in the room with me",
}


def diary_moments(timeline: list[dict], vision_stats: dict, zones_seen: set | None = None,
                  camera_window: tuple[str, str] | None = None) -> list[dict]:
    """The only things the diary is allowed to talk about, in order, in plain words.
    Back-to-back repeats (e.g. five locked food pulls) become one moment with a count."""
    moments: list[dict] = []
    last_camera = -1  # index of the last camera moment, where "no human came" belongs
    for r in timeline:
        if r["source"] == "camera":
            text = CAMERA_MOMENTS.get(r["what"], r["what"])
            if r["what"] in ("sleeping", "resting") and r.get("where") == "bed":
                text += " on my bed"
            key = ("camera", r["what"])
        else:
            text = r["moment"]
            key = ("hub", text)
        if moments and moments[-1]["_key"] == key:
            moments[-1]["times"] += 1
            if r["source"] == "camera":
                last_camera = len(moments) - 1
            continue
        m = {"_key": key, "when": _part_of_day(r["time"]), "moment": text, "times": 1}
        if r.get("seen"):
            m["what_the_photo_showed"] = r["seen"]
        if r["source"] == "camera" and r.get("minutes", 0) >= 60:
            m["how_long"] = "a long time"
        moments.append(m)
        if r["source"] == "camera":
            last_camera = len(moments) - 1

    if vision_stats.get("humans_detectable") and not vision_stats.get("human_seen_s") and camera_window:
        a, b = _part_of_day(camera_window[0]), _part_of_day(camera_window[1])
        moments.insert(last_camera + 1, {"_key": None, "when": a if a == b else f"{a} to {b}",
                                         "moment": "no human came to see me", "times": 1})

    for i, m in enumerate(moments, 1):
        m.pop("_key")
        m["id"] = i
        if m["times"] == 1:
            m.pop("times")
    return moments


DIARY_SYSTEM = """You write a dog's diary entry for today, in the dog's own voice.

You get a numbered list of MOMENTS: the only things that happened today. Tell the day through them, in
order, in plain dog words, and give each one a feeling (proud, bored, hopeful, cozy, lonely, grumpy,
happy...).

Strict rules:
- Use only the listed moments. You may skip some and merge repeats, but never add an action, place,
  object, person or event that isn't in a moment. If no moment says I sat by the door, I didn't. If no
  moment says my human came, don't say they did. "what_the_photo_showed" details are true and usable.
- Feelings, thoughts, wishes and dog-logic about the listed moments are yours to add. That is where the
  humour and sweetness come from.
- "times" means it happened that many times in a row: say "again and again", not the number.
- If a moment says no human came, say so gently and a little sadly, for that part of the day only.
- No numbers, no clock times, no lists. Never mention cameras, photos, sensors or data.

Tone: simple, sweet, gently funny. Short sentences and easy words, like a dog who loves their people.

Diary format: the date in italics on the first line, then "Dear Diary,", then 3-4 short paragraphs
(140-220 words). End with a one-line sign-off, then the dog's name and a paw: "<Name> 🐾".
Return the diary and the ids of every moment you used.

For context only (the dog never explains it, and just calls it "the hub" or "Laika"): {hub}"""

DIARY_SCHEMA = {
    "type": "object",
    "properties": {
        "diary": {"type": "string", "description": "The full diary entry in Markdown."},
        "used_moment_ids": {"type": "array", "items": {"type": "integer"}},
    },
    "required": ["diary", "used_moment_ids"],
    "additionalProperties": False,
}


def write_diary(dog: dict, date: str, moments: list[dict]) -> tuple[str, list[int]]:
    """Returns (diary markdown, ids of the moments Claude says it used)."""
    payload = {"dog": dog, "date": datetime.fromisoformat(date).strftime("%A, %d %B %Y"), "moments": moments}
    response = _client().beta.messages.create(
        model=_model(), max_tokens=16000, betas=[FALLBACK_BETA], fallbacks="default",
        thinking={"type": "adaptive"},
        output_config={"effort": "medium", "format": {"type": "json_schema", "schema": DIARY_SCHEMA}},
        system=DIARY_SYSTEM.format(hub=HUB_CONTEXT),
        messages=[{"role": "user", "content": "Today's moments. Write today's diary entry.\n\n"
                   + json.dumps(payload, indent=1)}],
    )
    out = json.loads(_text(response))
    return out["diary"], out["used_moment_ids"]


def offline_diary(dog: dict, date: str, vision_stats: dict, hub_counts: dict, time_scale: float = 1.0) -> str:
    """A plain fallback entry for when Claude isn't reachable."""
    name = dog.get("name", "Dog")
    day = datetime.fromisoformat(date).strftime("%A, %d %B %Y")
    mood = ("I played so much today, and every treat felt like a medal." if hub_counts.get("treats_confirmed")
            else "Today felt cozy and mostly quiet.")
    return (f"*{day}*\n\nDear Diary,\n\n{mood} But I had my people and my bed, and that is plenty.\n\n"
            f"Tomorrow I will love them just as much. Maybe more.\n\nWaggingly yours,\n{name} 🐾")
