"""Camera + diary integration with the Laika hub (no network, no camera, no Claude calls)."""
from datetime import datetime

import numpy as np
import pytest

from camera.detector import drop_person_lookalikes, mask_out_people
from camera.vision import Episode
from device_model import Hub
from diary import owner_report
from diary.claude import build_timeline, diary_moments, offline_diary
from diary.hub_events import drive, hub_stats, moment_for, simulate_hub_day

DAY = datetime(2026, 9, 27, 7, 0)


def ep(i, state, start, end, zone=None):
    return Episode(id=i, state=state, zone=zone, start_s=start, end_s=end, peak_speed=0, mean_motion=0,
                   keyframe_idx=0)


def test_drive_confirms_outputs_like_the_sensor():
    hub = Hub()
    drive(hub, {"type": "owner", "action": "offer", "feature": "tug"})
    for _ in range(6):
        drive(hub, {"type": "pull", "node": "N4", "force": 5.0, "duration_ms": 700})
    assert hub._counters()["treats_today"] == 1
    assert any(e["event"] == "OUTPUT_CONFIRMED" and e["output"] == "treat" for e in hub.events)


def test_hub_events_become_dog_moments():
    assert moment_for({"event": "GREETING"}) == "my human came home and the hub waved its ears hello"
    assert moment_for({"event": "REQUEST_CREATED", "request": "walk"}) == "booped the pad to ask for a walk"
    assert "go outside" in moment_for({"event": "REQUEST_CREATED", "request": "choice", "choice": "OUTSIDE"})
    assert moment_for({"event": "PULL_START"}) is None          # the dog doesn't notice internals
    assert moment_for({"event": "OUTPUT_CONFIRMED", "output": "roll"}) is None  # folded into BALL_RETURNED


def test_simulated_day_respects_hub_safety_limits():
    for persona in ("foodie", "athlete", "diva"):
        hub = simulate_hub_day(DAY, [], persona=persona)
        counts = hub_stats(hub, "2026-09-27")
        assert counts["treats_confirmed"] <= 8
        assert counts["greetings"] >= 1  # the owner "comes home" at 18:05 when the camera can't track people
        assert all(e["ts"].startswith("2026-09-27") for e in hub.events)


def test_camera_lines_up_with_hub_day():
    episodes = [ep(0, "tugging", 0, 60, "tug_device"), ep(1, "waiting_at_door", 60, 120, "door")]
    hub = simulate_hub_day(DAY, episodes, time_scale=1, persona="diva", seed=1)
    first = [e for e in hub.events if e["ts"] < "2026-09-27T07:05"]
    assert any(e["event"] == "SESSION_STARTED" for e in first)     # tugging on camera -> a tug round
    assert any(e["event"] == "FEATURE_OFFERED" and e.get("feature") == "walk" for e in first)


def test_diary_moments_only_contain_what_happened():
    hub = Hub()
    drive(hub, {"type": "camera", "event": "HUMAN_DETECTED", "confidence": 0.9, "ts": "2026-09-27T07:10:00"})
    timeline = build_timeline([ep(0, "sleeping", 0, 600, "bed")], hub.events, DAY)
    moments = diary_moments(timeline, {"humans_detectable": True, "human_seen_s": 0}, camera_window=("07:00", "07:10"))
    texts = [m["moment"] for m in moments]
    assert texts[0].startswith("had a nap on my bed")
    assert "my human came home and the hub waved its ears hello" in texts
    assert [m["id"] for m in moments] == list(range(1, len(moments) + 1))


def test_owner_report_and_offline_diary_build():
    hub = simulate_hub_day(DAY, [], persona="foodie")
    counts = hub_stats(hub, "2026-09-27")
    timeline = build_timeline([], hub.events, DAY)
    md = owner_report.build({"name": "Pablo"}, "2026-09-27", timeline, {"seconds_by_state": {}}, counts, [],
                            "x.mp4", 60, 1, synthetic_hub=True)
    assert "## Laika hub" in md and f"| Treats (sensor-confirmed) | {counts['treats_confirmed']} / 8 |" in md
    assert offline_diary({"name": "Pablo"}, "2026-09-27", {}, counts).rstrip().endswith("Pablo 🐾")


def test_people_are_never_the_dog():
    person = (0.1, 0.1, 0.5, 0.9, 0.9)
    assert drop_person_lookalikes([(0.12, 0.1, 0.5, 0.88, 0.4)], [person]) == []   # "dog" on top of a person
    assert drop_person_lookalikes([(0.6, 0.6, 0.9, 0.9, 0.8)], [person]) != []     # a real dog elsewhere
    mask = np.full((100, 100), 255, np.uint8)
    mask_out_people(mask, [person])
    assert mask[50, 30] == 0 and mask[50, 90] == 255


@pytest.mark.skipif(not __import__("camera.detector", fromlist=["x"]).DogDetector.available(),
                    reason="models/yolo11n.onnx not downloaded")
def test_detector_loads_and_runs():
    from camera.detector import DogDetector
    dogs, people = DogDetector().detect(np.zeros((360, 640, 3), np.uint8))
    assert dogs == [] and people == []


def test_api_camera_mode_shares_one_hub(tmp_path):
    """python -m api.server --camera: web app inputs, the camera and the diary all use one Hub."""
    from api.server import create_app
    from diary.live import App, build_parser
    live = App(build_parser().parse_args(["--offline", "--out", str(tmp_path)]))  # no capture thread started
    client = create_app(live=live).test_client()

    client.post("/input", json={"type": "owner", "action": "offer", "feature": "tug"})
    for _ in range(6):
        client.post("/input", json={"type": "pull", "node": "N4", "force": 5.0, "duration_ms": 700})
    state = client.get("/live").get_json()
    assert state["hub"]["treats"] == 1                          # sensor auto-confirmed, counted once
    assert state["hub"]["counts"]["valid_pulls"] == 6
    assert any("treat" in n for n in state["hub"]["notifications"])
    assert "the hub gave me a treat for a good tug round" in [m["moment"] for m in live.diary.moments]
    assert client.get("/state").get_json()["counters"]["treats_today"] == 1   # same hub via the plain API

    client.post("/diary/finish")
    days = client.get("/diary/days").get_json()
    assert len(days) == 1 and next(iter(days.values()))["text"].rstrip().endswith("🐾")
