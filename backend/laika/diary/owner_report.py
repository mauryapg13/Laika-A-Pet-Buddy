"""The owner-facing activity report: plain facts, built straight from the data (no LLM, so numbers are exact).
Camera behaviour + the Laika hub's own counters. The dog's diary is separate (claude.write_diary)."""
from __future__ import annotations

from laika.camera.vision import STATE_EMOJI, Episode

LABELS = {
    "sleeping": "Sleeping", "resting": "Resting", "wandering": "Walking around", "zoomies": "Zoomies",
    "playing": "Playing", "tugging": "Tugging at the hub", "eating": "At the food bowl",
    "waiting_at_door": "Waiting at the door", "away": "Out of view", "human_in_room": "Human in the room",
}


def observations(vision_stats: dict, hub: dict, time_scale: float) -> list[str]:
    """Simple, factual rules that flag things an owner might act on."""
    mins = {k: v * time_scale / 60 for k, v in vision_stats.get("seconds_by_state", {}).items()}
    obs = []
    if hub.get("lockouts"):
        obs.append(f"{hub['lockouts']} tug lockout(s): 5 high-force pulls within 20 s paused the strap for 10 min.")
    if hub.get("treats_confirmed", 0) >= 8:
        obs.append("Daily treat limit (8) reached.")
    if hub.get("requests_unanswered"):
        obs.append(f"{hub['requests_unanswered']} request(s) expired without an answer (10 min).")
    if hub.get("output_failures"):
        obs.append(f"{hub['output_failures']} output failure(s) (jam). Check the spout.")
    if hub.get("valid_pulls", 0) + hub.get("balls_rolled", 0) + hub.get("toys_tidied", 0) < 6:
        obs.append("Very little play on the hub today.")
    door = mins.get("waiting_at_door", 0)
    if door >= 10:
        obs.append(f"{door:.0f} min spent waiting at the door (camera); {hub.get('walk_requests', 0)} walk request(s).")
    if vision_stats.get("zoomies_bursts", 0) >= 3:
        obs.append(f"{vision_stats['zoomies_bursts']} zoomies bursts. High energy day.")
    if mins.get("sleeping", 0) == 0 and sum(mins.values()) > 120:
        obs.append("No sleep seen on camera during the recorded period.")
    if vision_stats.get("humans_detectable") and not vision_stats.get("human_seen_s"):
        obs.append("No person was seen with the dog on camera during the recorded period.")
    if vision_stats.get("most_dogs_in_frame", 0) > 1:
        obs.append(f"Up to {vision_stats['most_dogs_in_frame']} dogs in view at once; behaviour stats follow one dog.")
    return obs or ["Nothing unusual flagged today."]


def _grouped(timeline: list[dict]) -> list[dict]:
    """Collapse back-to-back identical hub rows (e.g. six tug pulls) into one row with a count."""
    out = []
    for r in timeline:
        if (out and r["source"] == "hub" and out[-1]["source"] == "hub"
                and out[-1]["moment"] == r["moment"]):
            out[-1]["n"] = out[-1].get("n", 1) + 1
        else:
            out.append(dict(r))
    return out


def build(dog: dict, date: str, timeline: list[dict], vision_stats: dict, hub: dict,
          episodes: list[Episode], video: str, video_duration_s: float, time_scale: float,
          synthetic_hub: bool) -> str:
    name = dog.get("name", "Dog")
    mins = {k: v * time_scale / 60 for k, v in vision_stats.get("seconds_by_state", {}).items()}
    total = sum(mins.values()) or 1
    L = [f"# Daily Activity Report: {name}", "", f"**Date:** {date}  ", f"**Dog:** {name}, {dog.get('breed', '')}, "
         f"age {dog.get('age_years', '?')}", "", "## Observations", ""]
    L += [f"- {o}" for o in observations(vision_stats, hub, time_scale)]

    L += ["", "## Time by behaviour (camera)", "", "| Behaviour | Minutes | Share |", "|---|---:|---:|"]
    for k, v in sorted(mins.items(), key=lambda kv: -kv[1]):
        L.append(f"| {STATE_EMOJI.get(k, '')} {LABELS.get(k, k)} | {v:.1f} | {v / total:.0%} |" if v < 10 else
                 f"| {STATE_EMOJI.get(k, '')} {LABELS.get(k, k)} | {v:.0f} | {v / total:.0%} |")
    L += ["", f"Longest nap: {vision_stats.get('longest_nap_s', 0) * time_scale / 60:.0f} min · "
          f"Zoomies bursts: {vision_stats.get('zoomies_bursts', 0)} · "
          f"Distance covered: {vision_stats.get('distance_room_widths', 0)} room widths · "
          f"Top speed: {vision_stats.get('top_speed_body_lengths_per_s', 0)} body lengths/s · "
          + ("Human time: " + (f"{vision_stats['human_seen_s'] * time_scale / 60:.1f} min"
                               if vision_stats.get("humans_detectable") else "not tracked"))]

    h = hub
    L += ["", "## Laika hub", "", "| Metric | Value |", "|---|---:|",
          f"| Treats (sensor-confirmed) | {h.get('treats_confirmed', 0)} / 8 |",
          f"| Valid tug pulls | {h.get('valid_pulls', 0)} |",
          f"| Balls rolled back | {h.get('balls_rolled', 0)} |",
          f"| Toys tidied | {h.get('toys_tidied', 0)} |",
          f"| Walk requests (boops) / walks released | {h.get('walk_requests', 0)} / {h.get('harness_releases', 0)} |",
          f"| My Choice picks | {', '.join(h.get('choices') or []) or '-'} |",
          f"| Requests unanswered | {h.get('requests_unanswered', 0)} |",
          f"| Arrival greetings | {h.get('greetings', 0)} |",
          f"| Lockouts / output failures | {h.get('lockouts', 0)} / {h.get('output_failures', 0)} |",
          f"| Ignored inputs | {h.get('ignored_inputs', 0)} |",
          f"| Learned pull threshold | {h.get('learned_pull_threshold_n', '-')} N |"]

    L += ["", "## Timeline", "", "| Time | Source | Event | Detail |", "|---|---|---|---|"]
    for r in _grouped(timeline):
        if r["source"] == "camera":
            detail = f"{r['minutes']:.1f} min" if r["minutes"] < 10 else f"{r['minutes']:.0f} min"
            if r.get("where"):
                detail += f", {r['where'].replace('_', ' ')}"
            if r.get("seen"):
                detail += f". Photo check: {r['seen']}"
            L.append(f"| {r['time']} | camera | {LABELS.get(r['what'], r['what'])} | {detail} |")
        else:
            L.append(f"| {r['time']} | hub | {r['event']}{' ×' + str(r['n']) if r.get('n') else ''} | "
                     f"{r['moment'][0].upper() + r['moment'][1:]}{'. ' + r['detail'] if r.get('detail') else ''} |")

    L += ["", "## Data notes", "",
          f"- Footage: `{video}`, {video_duration_s:.0f} s"
          + (f", stretched ×{time_scale:g} to represent the day" if time_scale != 1 else "") + ".",
          f"- {len(episodes)} behaviour episodes from OpenCV tracking; photo checks are Claude's reading of one "
          f"keyframe per episode.",
          "- Hub log: " + ("**simulated** (a real `laika.hub.Hub` driven by a synthetic day)." if synthetic_hub
                           else "from the Laika hub.")]
    return "\n".join(L)
