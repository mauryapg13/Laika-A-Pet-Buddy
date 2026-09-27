"""Bridge between the Laika hub (laika.hub.Hub) and the diary.

- `moment_for(event)`: a hub event in the dog's words ("the hub gave me a treat"), or None if the dog
  wouldn't notice it (PULL_START, SESSION_ENDED, ...).
- `simulate_hub_day(...)`: drives a real Hub through a plausible day for testing, lined up with what the
  camera saw. Every output is confirmed by a simulated sensor, the way the hardware will.
- `drive(hub, msg)`: send one input and auto-confirm any output it triggers (for live demos without hardware).
"""
from __future__ import annotations

import heapq
import random
from datetime import datetime, timedelta

from laika.hub import Hub
from laika.hub.config import CHOICES

CHOICE_WORDS = {"OUTSIDE": "go outside", "REST": "rest", "PLAY": "play"}

# What the hub is, for the diary writer (the dog never explains it, but Claude needs the picture).
HUB_CONTEXT = (
    "Laika, the dog's wall hub: a boop pad to ask for a walk, a strap with a bone tug that drops a treat "
    "after a good tug round, a ball pocket that rolls the ball back out, a basket for tidying toys, three "
    "choice ropes to tell the humans OUTSIDE / REST / PLAY, a button that plays calm music, and two soft "
    "ears that wave hello when the humans come home."
)

OUTPUT_ACTIONS = {"dispense_treat": "N5", "roll_ball": "N5", "release_harness": "N4"}


def moment_for(e: dict) -> str | None:
    """A hub event as the dog experienced it."""
    ev, detail = e["event"], str(e.get("detail", ""))
    if ev == "FEATURE_OFFERED":
        return {"tug": "my human put out the bone tug", "walk": "my human clipped my harness on the hub",
                "roll": "my human switched on the ball game",
                "choice": "my human set out my choice ropes"}.get(e.get("feature"))  # tidy: see TIDY_CUE
    if ev == "TIDY_CUE":
        return "my human asked me to tidy my toys"
    if ev == "PULL_VALID":
        return "pulled the bone tug"
    if ev == "OUTPUT_CONFIRMED":
        # (a confirmed ball roll is folded into BALL_RETURNED, so one fetch = one moment)
        return {"treat": "the hub gave me a treat for a good tug round",
                "harness": "my harness dropped down: walk time"}.get(e.get("output"))
    if ev == "OUTPUT_BLOCKED" and e.get("output") == "treat":
        return "finished a tug round but no treat came (enough treats for now)"
    if ev == "OUTPUT_FAILED":
        return "the hub got stuck and nothing came out"
    if ev == "SESSION_LOCKED_OUT":
        return "pulled too hard, too fast, so the hub put the tug away for a while"
    if ev == "REQUEST_CREATED":
        if e.get("request") == "walk":
            return "booped the pad to ask for a walk"
        return f"pulled a choice rope to say I want to {CHOICE_WORDS.get(e.get('choice'), 'do something')}"
    if ev == "REQUEST_EXPIRED":
        return "asked my human, but nobody answered"
    if ev == "HUMAN_CONFIRMED":
        return ("my human said yes to a walk" if e.get("request") == "walk"
                else f"my human said yes: we will {CHOICE_WORDS.get(e.get('choice'), 'do it')}")
    if ev == "BALL_RETURNED":
        return "dropped my ball in the hub and it rolled it back out to me"
    if ev == "TIDY_DEPOSIT":
        return "put a toy in the basket"
    if ev == "GREETING":
        return "my human came home and the hub waved its ears hello"
    if ev == "AUDIO_ON":
        return "turned on my calm music"
    if ev == "INPUT_IGNORED" and "parked" in detail.lower():
        return "tugged the strap but it was put away"
    return None


# Hub details worth showing the owner (the rest, like "toy 3", are just counters).
_KEEP_DETAIL = {"SESSION_LOCKED_OUT", "OUTPUT_BLOCKED", "OUTPUT_FAILED", "REQUEST_EXPIRED", "INPUT_IGNORED", "GREETING"}


def hub_timeline_rows(events: list[dict]) -> list[dict]:
    rows = []
    for e in events:
        m = moment_for(e)
        if m:
            keep = e["event"] in _KEEP_DETAIL and e.get("detail")
            rows.append({"time": e["ts"][11:16], "_ts": e["ts"], "source": "hub", "event": e["event"],
                         "moment": m, **({"detail": e["detail"]} if keep else {})})
    return rows


def drive(hub: Hub, msg: dict, sensor_delay_s: float = 2.0) -> list[dict]:
    """Send one input; if it asks the hardware for an output, confirm it like the sensor would.
    Returns every output JSON produced (1 or 2)."""
    out = hub.handle(msg)
    outs = [out]
    for a in out["actions"]:
        if a["do"] in OUTPUT_ACTIONS:
            ts = msg.get("ts")
            confirm_ts = ((datetime.fromisoformat(ts) + timedelta(seconds=sensor_delay_s)).isoformat(timespec="seconds")
                          if ts else None)
            outs.append(hub.handle({"type": "output_confirmed", "node": OUTPUT_ACTIONS[a["do"]],
                                    **({"ts": confirm_ts} if confirm_ts else {})}))
    return outs


# ------------------------------------------------------------------ synthetic day (testing without hardware)
PERSONAS = {  # relative appetite for each hub game
    "foodie": {"tug": 3.0, "roll": 0.8, "tidy": 0.4, "walk": 0.8, "choice": 0.5, "frantic": 0.25},
    "athlete": {"tug": 2.0, "roll": 2.5, "tidy": 0.6, "walk": 1.5, "choice": 0.6, "frantic": 0.1},
    "diva": {"tug": 0.8, "roll": 0.6, "tidy": 0.3, "walk": 2.0, "choice": 1.5, "frantic": 0.05},
}


def _tug_round(t: datetime, rng, reps: int = 8) -> list[tuple[datetime, dict]]:
    """A few extra pulls, since some come out too weak or too short to count."""
    msgs = [(t, {"type": "owner", "action": "offer", "feature": "tug"})]
    for i in range(reps):
        t += timedelta(seconds=rng.randint(6, 15))
        msgs.append((t, {"type": "pull", "node": "N4", "force": round(rng.uniform(4.5, 8.5), 1),
                         "duration_ms": rng.randint(400, 1500)}))
    msgs.append((t + timedelta(seconds=20), {"type": "release", "node": "N4"}))
    return msgs


def _frantic(t: datetime, rng) -> list[tuple[datetime, dict]]:
    msgs = [(t, {"type": "owner", "action": "offer", "feature": "tug"})]
    for i in range(5):
        msgs.append((t + timedelta(seconds=3 * (i + 1)),
                     {"type": "pull", "node": "N4", "force": round(rng.uniform(12.5, 16), 1), "duration_ms": 900}))
    msgs.append((t + timedelta(seconds=30), {"type": "release", "node": "N4"}))
    return msgs


def _walk(t: datetime, rng, answered: bool = True) -> list[tuple[datetime, dict]]:
    msgs = [(t, {"type": "owner", "action": "offer", "feature": "walk"}),
            (t + timedelta(minutes=rng.randint(2, 20)), {"type": "boop", "duration_ms": 300})]
    if answered:
        msgs.append((msgs[-1][0] + timedelta(minutes=rng.randint(1, 8)), {"type": "button", "node": "N1"}))
    return msgs


def _roll(t: datetime, rng) -> list[tuple[datetime, dict]]:
    msgs = [(t, {"type": "owner", "action": "offer", "feature": "roll"})]
    for i in range(rng.randint(2, 7)):
        t += timedelta(seconds=rng.randint(15, 60))
        msgs.append((t, {"type": "ball_in"}))
    return msgs


def _tidy(t: datetime, rng) -> list[tuple[datetime, dict]]:
    msgs = [(t, {"type": "button", "node": "N1"})]
    for i in range(rng.randint(1, 4)):
        msgs.append((t + timedelta(seconds=20 * (i + 1)), {"type": "toy_in_basket"}))
    return msgs


def _choice(t: datetime, rng) -> list[tuple[datetime, dict]]:
    slot = rng.choice(list(CHOICES))
    return [(t, {"type": "owner", "action": "offer", "feature": "choice"}),
            (t + timedelta(minutes=rng.randint(1, 10)),
             {"type": "pull", "node": slot, "force": round(rng.uniform(3.5, 6), 1), "duration_ms": 700}),
            (t + timedelta(minutes=rng.randint(11, 14)), {"type": "button", "node": "N1"}),
            (t + timedelta(minutes=15), {"type": "owner", "action": "park"})]


def simulate_hub_day(day_start: datetime, camera_episodes: list, time_scale: float = 1.0,
                     human_visits: list | None = None, humans_tracked: bool = False,
                     persona: str = "foodie", seed: int = 7) -> Hub:
    """Plays a whole day of inputs through a real Hub and returns it (hub.events is the log).

    Lined up with the camera: tugging on camera -> a tug round, waiting at the door -> a walk request,
    people seen -> HUMAN_DETECTED. If the camera can't track people, the owner "comes home" at 18:05."""
    rng = random.Random(seed)
    rates = PERSONAS[persona]
    plan: list[tuple[datetime, dict]] = []

    for e in camera_episodes:
        at = day_start + timedelta(seconds=e.start_s * time_scale)
        if e.state == "tugging":
            plan += _tug_round(at, rng)
        elif e.state == "waiting_at_door":
            plan += _walk(at, rng, answered=rng.random() < 0.7)
    for a, _ in human_visits or []:
        plan.append((day_start + timedelta(seconds=a * time_scale),
                     {"type": "camera", "event": "HUMAN_DETECTED", "confidence": 0.91}))
    if not humans_tracked:
        plan.append((day_start.replace(hour=18, minute=5), {"type": "camera", "event": "HUMAN_DETECTED",
                                                            "confidence": 0.92}))

    # Background games through the day, busiest mornings and evenings.
    t = day_start.replace(hour=7, minute=0, second=0)
    end = day_start.replace(hour=21, minute=30)
    makers = {"tug": _tug_round, "roll": _roll, "tidy": _tidy, "walk": _walk, "choice": _choice, "frantic": _frantic}
    while t < end:
        busy = 1.5 if t.hour in (7, 8, 17, 18, 19) else 0.5
        for game, rate in rates.items():
            if rng.random() < rate * busy / 12:
                plan += makers[game](t + timedelta(seconds=rng.randint(0, 599)), rng)
        t += timedelta(minutes=10)

    hub = Hub()
    queue = [(when, i, msg) for i, (when, msg) in enumerate(plan)]
    heapq.heapify(queue)
    while queue:
        when, _, msg = heapq.heappop(queue)
        drive(hub, {**msg, "ts": when.isoformat(timespec="seconds")})
    hub.handle({"type": "tick", "ts": end.isoformat(timespec="seconds")})
    return hub


def hub_stats(hub: Hub, day: str) -> dict:
    s = hub.summary(day)
    c = dict(s["counts"])
    events = [e for e in hub.events if e["ts"].startswith(day)]
    c["requests_unanswered"] = sum(e["event"] == "REQUEST_EXPIRED" for e in events)
    c["walk_requests"] = sum(e["event"] == "REQUEST_CREATED" and e.get("request") == "walk" for e in events)
    c["choices"] = [e.get("choice") for e in events if e["event"] == "REQUEST_CREATED" and e.get("request") == "choice"]
    c["play_offers"] = sum(e["event"] == "FEATURE_OFFERED" for e in events)
    c["learned_pull_threshold_n"] = hub.threshold.value
    return c
