import json
from datetime import datetime, timedelta

import pytest

from device_model import Hub
from device_model.config import LIMITS as L
from device_model.ml import ActivityAnomaly, ThresholdLearner

ANOMALY = ActivityAnomaly()  # train once for all tests
T0 = datetime(2026, 9, 27, 10, 0, 0)


class Clock:
    def __init__(self):
        self.t = T0

    def __call__(self, seconds=0):
        self.t += timedelta(seconds=seconds)
        return self.t.isoformat()


@pytest.fixture
def hc():
    return Hub(anomaly=ANOMALY), Clock()


def send(hub, clock, advance=1, **msg):
    return hub.handle({**msg, "ts": clock(advance)})


def names(out):
    return [e["event"] for e in out["events"]]


def tug_pulls(hub, clock, n, force=5.0):
    out = None
    for _ in range(n):
        out = send(hub, clock, type="pull", node="N4", force=force, duration_ms=600)
    return out


# ---------------------------------------------------------------- output contract
def test_output_is_json_with_fixed_shape(hc):
    hub, c = hc
    out = send(hub, c, type="tick")
    json.dumps(out)
    for key in ("ts", "device_state", "mode", "nodes", "ears", "halo", "actions", "events",
                "notifications", "counters", "ml"):
        assert key in out
    assert set(out["nodes"]) == {"BOOP", "N1", "N2", "N3", "N4", "N5"}


# ---------------------------------------------------------------- F4 tug -> treat
def test_tug_gives_one_treat_after_six_valid_pulls(hc):
    hub, c = hc
    out = send(hub, c, type="owner", action="offer", feature="tug")
    assert out["nodes"]["N4"]["state"] == "READY" and out["nodes"]["N4"]["attachment"] == "bone_tug"
    out = tug_pulls(hub, c, 5)
    assert out["nodes"]["N4"]["state"] == "ACTIVE" and out["counters"]["tug_reps"] == 5
    out = tug_pulls(hub, c, 1)
    assert {"do": "dispense_treat", "node": "N5"} in out["actions"]
    assert out["nodes"]["N4"]["state"] == "COOLDOWN"
    # treat only counts once the sensor confirms it
    assert out["counters"]["treats_today"] == 0
    out = send(hub, c, type="output_confirmed", node="N5")
    assert out["counters"]["treats_today"] == 1 and out["notifications"]
    out = send(hub, c, type="release", node="N4")
    assert out["nodes"]["N4"]["state"] == "PARKED" and out["mode"] == "idle"


def test_harder_pull_gives_nothing_extra_and_parked_pull_is_ignored(hc):
    hub, c = hc
    out = send(hub, c, type="pull", node="N4", force=11, duration_ms=600)
    assert "INPUT_IGNORED" in names(out) and not out["actions"]
    send(hub, c, type="owner", action="offer", feature="tug")
    out = send(hub, c, type="pull", node="N4", force=11, duration_ms=600)
    assert out["counters"]["tug_reps"] == 1  # one rep, no matter how hard


def test_weak_pull_does_not_count(hc):
    hub, c = hc
    send(hub, c, type="owner", action="offer", feature="tug")
    out = send(hub, c, type="pull", node="N4", force=1.0, duration_ms=600)
    assert out["counters"]["tug_reps"] == 0 and "INPUT_IGNORED" in names(out)


def test_treat_limits_hourly(hc):
    hub, c = hc
    for i in range(L["treats_per_hour"] + 1):
        send(hub, c, type="owner", action="offer", feature="tug")
        out = tug_pulls(hub, c, 6)
        if i < L["treats_per_hour"]:
            send(hub, c, type="output_confirmed")
        else:
            assert "OUTPUT_BLOCKED" in names(out) and not any(a["do"] == "dispense_treat" for a in out["actions"])
        send(hub, c, type="release")
    assert hub.state()["counters"]["treats_today"] == L["treats_per_hour"]


def test_jam_is_failure_not_success_and_no_retry(hc):
    hub, c = hc
    send(hub, c, type="owner", action="offer", feature="tug")
    tug_pulls(hub, c, 6)
    out = send(hub, c, type="output_failed", reason="jam")
    assert "OUTPUT_FAILED" in names(out) and out["nodes"]["N5"]["state"] == "FAULT"
    assert out["counters"]["treats_today"] == 0 and not out["actions"]


def test_frantic_pulls_lock_out(hc):
    hub, c = hc
    send(hub, c, type="owner", action="offer", feature="tug")
    out = None
    for _ in range(L["frantic_pulls"]):
        out = send(hub, c, advance=2, type="pull", node="N4", force=15, duration_ms=500)
    assert out["nodes"]["N4"]["state"] == "LOCKOUT" and "SESSION_LOCKED_OUT" in names(out)
    assert "high-force pulls" in out["notifications"][0]
    out = send(hub, c, type="owner", action="offer", feature="tug")
    assert out["mode"] == "idle"  # cannot re-offer during lockout
    out = send(hub, c, advance=L["lockout_s"] + 1, type="tick")
    assert out["nodes"]["N4"]["state"] == "PARKED"


def test_tug_session_time_limit(hc):
    hub, c = hc
    send(hub, c, type="owner", action="offer", feature="tug")
    tug_pulls(hub, c, 2)
    out = send(hub, c, advance=L["tug_session_max_s"] + 5, type="tick")
    assert out["nodes"]["N4"]["state"] == "COOLDOWN"


# ---------------------------------------------------------------- F5 walk
def test_walk_needs_owner_confirm(hc):
    hub, c = hc
    out = send(hub, c, type="boop")
    assert "INPUT_IGNORED" in names(out)  # no harness clipped
    send(hub, c, type="owner", action="offer", feature="walk")
    out = send(hub, c, type="boop")
    assert "REQUEST_CREATED" in names(out) and out["nodes"]["N1"]["state"] == "WAITING_CONFIRM"
    assert not any(a["do"] == "release_harness" for a in out["actions"])
    out = send(hub, c, type="boop")
    assert "INPUT_IGNORED" in names(out)  # repeat boops ignored
    out = send(hub, c, type="button", node="N1")
    assert {"do": "release_harness", "node": "N4"} in out["actions"] and out["ears"] == "wave"
    out = send(hub, c, type="output_confirmed", node="N4")
    assert out["mode"] == "idle" and "Harness released" in out["notifications"][0]


def test_walk_request_expires(hc):
    hub, c = hc
    send(hub, c, type="owner", action="offer", feature="walk")
    send(hub, c, type="boop")
    out = send(hub, c, advance=L["request_expiry_s"] + 1, type="tick")
    assert "REQUEST_EXPIRED" in names(out)


# ---------------------------------------------------------------- F6 arrival
def test_arrival_greeting_once(hc):
    hub, c = hc
    out = send(hub, c, type="camera", event="HUMAN_DETECTED", confidence=0.4)
    assert "GREETING" not in names(out)
    out = send(hub, c, type="camera", event="HUMAN_DETECTED", confidence=0.92)
    assert "GREETING" in names(out) and out["ears"] == "wave" and out["halo"] == "warm_pulse"
    out = send(hub, c, advance=60, type="camera", event="HUMAN_DETECTED", confidence=0.95)
    assert "GREETING" not in names(out)
    out = send(hub, c, type="tick")
    assert out["ears"] == "neutral"  # back to rest


# ---------------------------------------------------------------- F1 my choice
def test_my_choice_one_selection_then_confirm(hc):
    hub, c = hc
    send(hub, c, type="owner", action="offer", feature="choice")
    out = send(hub, c, type="pull", node="C_LEFT", force=4, duration_ms=600)
    assert out["choice_slots"]["C_LEFT"]["light"] and "OUTSIDE" in out["notifications"][0]
    out = send(hub, c, type="pull", node="C_RIGHT", force=4, duration_ms=600)
    assert "INPUT_IGNORED" in names(out)
    out = send(hub, c, type="button", node="N1")
    assert "HUMAN_CONFIRMED" in names(out)


# ---------------------------------------------------------------- F2 roll again
def test_roll_again(hc):
    hub, c = hc
    out = send(hub, c, type="ball_in")
    assert "INPUT_IGNORED" in names(out)
    send(hub, c, type="owner", action="offer", feature="roll")
    for i in range(3):
        out = send(hub, c, advance=5, type="ball_in")
        assert {"do": "roll_ball", "node": "N5"} in out["actions"]
        out = send(hub, c, type="output_confirmed")
    assert out["counters"]["rolls_session"] == 3
    out = send(hub, c, advance=L["roll_idle_timeout_s"] + 1, type="tick")
    assert out["mode"] == "idle"


# ---------------------------------------------------------------- F3 tidy
def test_tidy_together(hc):
    hub, c = hc
    out = send(hub, c, type="button", node="N1")
    assert out["mode"] == "tidy" and "TIDY_CUE" in names(out)
    out = send(hub, c, type="toy_in_basket")
    assert out["halo"] == "glow" and out["ears"] == "wave" and out["counters"]["toys_tidied_session"] == 1
    out = send(hub, c, advance=L["tidy_window_s"] + 1, type="tick")
    assert out["mode"] == "idle"


# ---------------------------------------------------------------- N2 audio + owner controls
def test_audio_toggle_and_auto_off(hc):
    hub, c = hc
    out = send(hub, c, type="button", node="N2")
    assert out["nodes"]["N2"]["state"] == "ON"
    out = send(hub, c, type="button", node="N2")
    assert out["nodes"]["N2"]["state"] == "OFF"
    send(hub, c, type="button", node="N2")
    out = send(hub, c, advance=L["audio_max_s"] + 1, type="tick")
    assert out["nodes"]["N2"]["state"] == "OFF"


def test_emergency_stop_and_reset(hc):
    hub, c = hc
    send(hub, c, type="owner", action="offer", feature="tug")
    out = send(hub, c, type="owner", action="stop")
    assert out["device_state"] == "FAULT" and {"do": "stop_motors"} in out["actions"]
    out = send(hub, c, type="pull", node="N4", force=5, duration_ms=600)
    assert "INPUT_IGNORED" in names(out)
    out = send(hub, c, type="owner", action="reset")
    assert out["device_state"] == "ONLINE"


def test_treats_can_be_disabled(hc):
    hub, c = hc
    send(hub, c, type="owner", action="treats_off")
    send(hub, c, type="owner", action="offer", feature="tug")
    out = tug_pulls(hub, c, 6)
    assert "OUTPUT_BLOCKED" in names(out)


def test_unknown_input_rejected(hc):
    hub, c = hc
    assert "INPUT_REJECTED" in names(send(hub, c, type="dance"))


# ---------------------------------------------------------------- ML
def test_threshold_learner_is_bounded():
    t = ThresholdLearner(3.0, (2.0, 8.0))
    assert t.value == 3.0
    for f in [6, 6.5, 7, 6.2, 6.8]:
        t.observe(f)
    assert 3.0 < t.value <= 8.0
    t2 = ThresholdLearner(3.0, (2.0, 8.0))
    for f in [30] * 10:
        t2.observe(f)
    assert t2.value == 8.0


def test_anomaly_flags_unusual_hour():
    assert ANOMALY.check({"boops": 0, "pulls": 4, "treats": 0, "rolls": 1, "tidy": 0, "ignored": 1}) is None
    msg = ANOMALY.check({"boops": 15, "pulls": 40, "treats": 3, "rolls": 1, "tidy": 0, "ignored": 30})
    assert msg and "pulls" in msg


def test_idle_suggestion(hc):
    hub, c = hc
    send(hub, c, type="boop")
    out = send(hub, c, advance=L["idle_suggest_s"] + 60, type="tick")
    assert out["ml"]["suggestion"]


def test_daily_summary_uses_confirmed_outputs_only(hc):
    hub, c = hc
    send(hub, c, type="owner", action="offer", feature="tug")
    tug_pulls(hub, c, 6)
    send(hub, c, type="output_failed")
    s = hub.summary()
    assert s["counts"]["treats_confirmed"] == 0 and s["counts"]["output_failures"] == 1
    send(hub, c, type="camera", event="BARK_EVENT", confidence=0.66)
    assert hub.summary()["camera"][0]["confidence"] == 0.66


# ---------------------------------------------------------------- HTTP API
def test_http_api():
    from api.server import create_app
    client = create_app(Hub(anomaly=ANOMALY)).test_client()
    out = client.post("/input", json={"type": "owner", "action": "offer", "feature": "walk", "ts": T0.isoformat()}).get_json()
    assert out["mode"] == "walk"
    outs = client.post("/input", json=[{"type": "boop"}, {"type": "button", "node": "N1"}]).get_json()
    assert len(outs) == 2 and outs[1]["actions"][0]["do"] == "release_harness"
    assert client.get("/state").get_json()["device_state"] == "ONLINE"
    assert "counts" in client.get("/summary").get_json()
    assert client.get("/events?limit=3").get_json()
    assert "N1" in client.get("/layout").get_json()["nodes"]
    assert client.post("/input", data="nope").status_code == 400
    assert client.get("/state").headers["Access-Control-Allow-Origin"] == "*"
