"""Laika camera + diary: camera footage + the Laika hub's event log -> the dog's diary and the owner's report.

    python -m diary data/videos/synthetic_day.mp4 --name Pablo --breed "beagle mix" \
        --start 07:00 --time-scale 280 --persona foodie

Hub events come from --hub-events (a JSON list, e.g. saved from GET /events), --hub-url (a running
`python -m api.server`), or, if neither is given, a real Hub driven through a simulated day.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import anthropic

from camera.config import VisionConfig
from camera.vision import analyze_video

from . import owner_report
from .claude import (build_timeline, caption_keyframes, credentials_available, diary_moments, offline_diary,
                     write_diary)
from .env import load_dotenv
from .hub_events import PERSONAS, hub_stats, simulate_hub_day


_THEME = """:root{--bg:#fffaf2;--fg:#2b2118;--muted:#7a6a58;--card:#fff;--line:#eadfce;--accent:#c0662a}
@media (prefers-color-scheme:dark){:root{--bg:#1d1813;--fg:#f3eadf;--muted:#b6a48f;--card:#2a221b;--line:#3d3228;--accent:#f0a24a}}
*{box-sizing:border-box} body{background:var(--bg);color:var(--fg);margin:0;padding:32px 16px}"""


def render_diary_html(markdown_text: str, dog_name: str) -> str:
    import html
    import markdown  # imported here so the rest of the pipeline works without it
    body = markdown.markdown(markdown_text)
    return f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(dog_name)}'s Diary</title><style>{_THEME}
main{{max-width:620px;margin:auto;background:var(--card);border:1px solid var(--line);border-radius:6px;
  padding:40px 36px;box-shadow:0 2px 14px rgba(0,0,0,.06);
  background-image:repeating-linear-gradient(transparent 0 31px,var(--line) 31px 32px);background-position:0 20px}}
p{{font:19px/32px Georgia,'Iowan Old Style',serif;margin:0 0 32px}} p:first-child em{{color:var(--accent)}}
@media (max-width:480px){{main{{padding:28px 20px}} p{{font-size:17px}}}}
</style></head><body><main>{body}</main></body></html>"""


def render_report_html(markdown_text: str, keyframes: list, dog_name: str) -> str:
    import html
    import markdown
    body = markdown.markdown(markdown_text, extensions=["tables"])
    gallery = "".join(
        f'<figure><img src="{html.escape(Path(e.keyframe_path).relative_to(Path(e.keyframe_path).parents[1]).as_posix())}">'
        f"<figcaption><b>{html.escape(e.state.replace('_', ' '))}</b> {html.escape(e.caption or '')}</figcaption></figure>"
        for e in keyframes)
    return f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(dog_name)} Activity Report</title><style>{_THEME}
body{{font:15px/1.5 -apple-system,system-ui,sans-serif}} main{{max-width:860px;margin:auto}}
h1{{font-size:1.6rem}} h2{{font-size:1.1rem;margin-top:2em;border-bottom:1px solid var(--line);padding-bottom:4px}}
.tbl{{overflow-x:auto}} table{{border-collapse:collapse;width:100%;font-size:.9rem}}
td,th{{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}}
code{{font-size:.85em}} .gallery{{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px}}
figure{{margin:0;background:var(--card);border:1px solid var(--line);border-radius:8px;overflow:hidden}}
figure img{{width:100%;display:block}} figcaption{{padding:8px;font-size:.8rem;color:var(--muted)}}
</style></head><body><main>{body.replace("<table>", '<div class="tbl"><table>').replace("</table>", "</table></div>")}
<h2>Keyframes</h2><div class="gallery">{gallery}</div></main></body></html>"""


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m diary", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--name", default="Pablo")
    ap.add_argument("--breed", default="good dog of unknown origin")
    ap.add_argument("--age", default="3")
    ap.add_argument("--quirks", default="", help="free text the report can riff on, e.g. 'afraid of the vacuum'")
    ap.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    ap.add_argument("--start", default="07:00", help="wall-clock time the video starts, HH:MM")
    ap.add_argument("--time-scale", type=float, default=1.0,
                    help="video seconds -> real seconds. Use >1 to let a short test clip stand in for a whole day.")
    ap.add_argument("--hub-events", help="JSON list of Laika hub events (e.g. saved from GET /events)")
    ap.add_argument("--hub-url", help="fetch events from a running hub API, e.g. http://localhost:5050")
    ap.add_argument("--persona", choices=list(PERSONAS), default="foodie", help="habits for the simulated hub day")
    ap.add_argument("--sample-fps", type=float, default=2.0)
    ap.add_argument("--zones", help="JSON of {zone: [x1, y1, x2, y2]} (normalized). "
                                    "Defaults to <video>.zones.json if it exists, else config.DEFAULT_ZONES.")
    ap.add_argument("--out", default="out")
    ap.add_argument("--debug-video", action="store_true", help="write an annotated tracking video")
    ap.add_argument("--no-captions", action="store_true", help="skip Claude vision on keyframes")
    ap.add_argument("--offline", action="store_true", help="no Claude calls; plain diary entry")
    args = ap.parse_args(argv)
    load_dotenv()

    out = Path(args.out) / f"{args.date}_{args.name.lower()}"
    out.mkdir(parents=True, exist_ok=True)
    start = datetime.fromisoformat(f"{args.date}T{args.start}")

    print(f"[1/4] Watching {args.video} at {args.sample_fps} snapshots/s ...")
    cfg = VisionConfig(sample_fps=args.sample_fps)
    zones_file = Path(args.zones) if args.zones else Path(args.video).with_suffix(".zones.json")
    if zones_file.exists():
        cfg.zones = {k: tuple(v) for k, v in json.loads(zones_file.read_text()).items()}
        print(f"      zones from {zones_file}: {', '.join(cfg.zones)}")
    vision = analyze_video(args.video, out, cfg, debug_video=args.debug_video)
    print(f"      {len(vision.snapshots)} snapshots -> {len(vision.episodes)} episodes: "
          + ", ".join(f"{k} {v}s" for k, v in vision.stats["seconds_by_state"].items()))

    print("[2/4] Loading the Laika hub's events ...")
    from device_model import Hub
    hub = Hub()
    if args.hub_events or args.hub_url:
        if args.hub_url:
            from urllib.request import urlopen
            with urlopen(args.hub_url.rstrip("/") + "/events?limit=1000000") as r:
                hub.events = json.loads(r.read())
        else:
            hub.events = json.loads(Path(args.hub_events).read_text())
    else:
        hub = simulate_hub_day(start, vision.episodes, args.time_scale, vision.human_visits,
                               humans_tracked=vision.stats.get("humans_detectable", False), persona=args.persona)
        print(f"      (simulated '{args.persona}' day through device_model.Hub)")
    (out / "hub_events.json").write_text(json.dumps(hub.events, indent=1))
    hub_counts = hub_stats(hub, args.date)
    print(f"      {len(hub.events)} hub events: {hub_counts['treats_confirmed']} treats, "
          f"{hub_counts['balls_rolled']} ball rolls, {hub_counts['walk_requests']} walk requests, "
          f"{hub_counts['greetings']} greetings")

    offline = args.offline
    if not offline and not credentials_available():
        print("      No Anthropic credentials found (set ANTHROPIC_API_KEY). Using the offline template report.",
              file=sys.stderr)
        offline = True
    if not offline and not args.no_captions:
        print("[3/4] Asking Claude what's in the keyframes ...")
        try:
            caption_keyframes(vision.episodes)
        except anthropic.AuthenticationError:
            print("      No valid Anthropic credentials; falling back to offline report.", file=sys.stderr)
            offline = True
        except (anthropic.APIError, RuntimeError, ValueError) as e:
            print(f"      Captioning failed ({e.__class__.__name__}: {e}); continuing without captions.", file=sys.stderr)
    else:
        print("[3/4] Skipping keyframe captions.")

    (out / "vision.json").write_text(json.dumps(vision.to_dict(), indent=1))
    timeline = build_timeline(vision.episodes, [e for e in hub.events if e["ts"].startswith(args.date)],
                              start, args.time_scale, vision.human_visits)
    (out / "timeline.json").write_text(json.dumps(timeline, indent=1))

    dog = {"name": args.name, "breed": args.breed, "age_years": args.age, "quirks": args.quirks}
    print("[4/4] Writing the diary and the activity report ...")
    diary = None
    watched = (start.strftime("%H:%M"),
               (start + timedelta(seconds=vision.duration_s * args.time_scale)).strftime("%H:%M"))
    moments = diary_moments(timeline, vision.stats, camera_window=watched)
    if not offline:
        try:
            diary, used = write_diary(dog, args.date, moments)
            known = {m["id"] for m in moments}
            if set(used) - known:
                print(f"      Warning: diary cites unknown moments {sorted(set(used) - known)}", file=sys.stderr)
            (out / "diary_moments.json").write_text(json.dumps(
                {"moments": moments, "used_moment_ids": used}, indent=1))
        except anthropic.AuthenticationError:
            print("      No valid Anthropic credentials; using a plain diary entry.", file=sys.stderr)
        except (anthropic.APIError, RuntimeError, ValueError) as e:
            print(f"      Diary call failed ({e.__class__.__name__}: {e}); using a plain entry.", file=sys.stderr)
    if diary is None:
        diary = offline_diary(dog, args.date, vision.stats, hub_counts, args.time_scale)
    report = owner_report.build(dog, args.date, timeline, vision.stats, hub_counts, vision.episodes,
                                args.video, vision.duration_s, args.time_scale,
                                synthetic_hub=not (args.hub_events or args.hub_url))

    (out / "diary.md").write_text(diary)
    (out / "report.md").write_text(report)
    shown = [e for e in vision.episodes if e.keyframe_path and e.state != "away"]
    try:
        (out / "diary.html").write_text(render_diary_html(diary, args.name))
        (out / "report.html").write_text(render_report_html(report, shown, args.name))
    except ImportError:
        pass
    print(f"\nDone.\n  Diary:  {out / 'diary.html'}\n  Report: {out / 'report.html'}\n  Data:   {out}/")


if __name__ == "__main__":
    main()
