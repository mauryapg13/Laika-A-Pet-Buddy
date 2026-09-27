"""PawHub device brain. `Hub.handle(input_json) -> output_json`.

Deterministic rules first (PRD): one valid action -> one outcome, cooldowns ignore repeats,
harder pulls never give more, unavailable = parked, outputs only count when sensor-confirmed,
harness release needs the owner's N1 press. ML only personalises the pull threshold,
spots unusual hours and suggests activities.
"""
import itertools
from datetime import datetime, timedelta
from typing import Optional

from .config import ATTACHMENT_FOR, CHOICES, FEATURES, LIMITS as L
from .ml import ActivityAnomaly, ThresholdLearner, daily_summary

# strap (N4) states, PRD 9.3
PARKED, READY, ACTIVE, COOLDOWN, RETRACTING, LOCKOUT, FAULT = (
    "PARKED", "READY", "ACTIVE", "COOLDOWN", "RETRACTING", "LOCKOUT", "FAULT")


class Hub:
    def __init__(self, anomaly: Optional[ActivityAnomaly] = None):
        self.now = datetime.now()
        self.device_state = "ONLINE"
        self.mode = "idle"                 # idle | tug | walk | choice | roll | tidy
        self.n4 = {"state": PARKED, "attachment": None, "resistance": 0}
        self.n5 = "IDLE"                   # IDLE | BUSY | FAULT
        self.pending_output = None         # {"output": "treat"|"roll"|"harness", "since": dt}
        self.pending_confirm = None        # {"kind": "walk"|"choice", "choice": str, "since": dt}
        self.session = None                # per-feature session data
        self.lockout_until = None
        self.boop_cooldown_until = None
        self.last_greet = None
        self.greeting_enabled = True
        self.treats_enabled = True
        self.audio_on_since = None
        self.last_dog_activity = None
        self.suggested_at = None
        self._anomaly_at, self._anomaly = None, None
        self.high_force_pulls = []
        self.events = []
        self._ids = itertools.count(1)
        self.threshold = ThresholdLearner(L["threshold_default_n"], L["threshold_bounds_n"])
        self.anomaly = anomaly if anomaly is not None else ActivityAnomaly()
        self._reset_output()

    # ------------------------------------------------------------------ API
    def handle(self, msg: dict) -> dict:
        """Process one input message and return the full device state as JSON-ready dict."""
        self._reset_output()
        if msg.get("ts"):
            self.now = datetime.fromisoformat(msg["ts"])
        else:
            self.now = datetime.now()
        self._timeouts()
        kind = msg.get("type")
        handler = {
            "pull": self._pull, "release": self._release, "boop": self._boop, "button": self._button,
            "ball_in": self._ball_in, "toy_in_basket": self._toy_in_basket, "camera": self._camera,
            "output_confirmed": self._output_confirmed, "output_failed": self._output_failed,
            "owner": self._owner, "tick": lambda m: None,
        }.get(kind)
        if handler is None:
            self._event("INPUT_REJECTED", detail=f"unknown input type {kind!r}")
        elif self.device_state == "FAULT" and kind not in ("owner", "tick", "camera"):
            self._event("INPUT_IGNORED", detail="device in FAULT - owner reset required")
        else:
            handler(msg)
        return self.state()

    def summary(self, day: Optional[str] = None) -> dict:
        return daily_summary(self.events, day or self.now.date().isoformat())

    def state(self) -> dict:
        slots = None
        if self.mode == "choice":
            chosen = (self.pending_confirm or {}).get("slot")
            slots = {k: {**v, "light": k == chosen} for k, v in CHOICES.items()}
        return {
            "ts": self.now.isoformat(timespec="seconds"),
            "device_state": self.device_state,
            "mode": self.mode,
            "nodes": {
                "BOOP": {"role": "walk_request", "state": "COOLDOWN" if self._boop_cooling() else
                         ("ENABLED" if self.mode == "walk" else "IDLE")},
                "N1": {"role": "owner_confirm", "state": "WAITING_CONFIRM" if self.pending_confirm else "IDLE"},
                "N2": {"role": "audio", "state": "ON" if self.audio_on_since else "OFF"},
                "N3": {"role": "ball_pocket", "state": "ACTIVE" if self.mode == "roll" else "PARKED"},
                "N4": {"role": "strap", **self.n4},
                "N5": {"role": "output", "state": self.n5},
            },
            "choice_slots": slots,
            "ears": self.out["ears"],
            "halo": self.out["halo"],
            "actions": self.out["actions"],
            "events": self.out["events"],
            "notifications": self.out["notifications"],
            "counters": self._counters(),
            "ml": {"pull_threshold_n": self.threshold.value, "anomaly": self.out["anomaly"],
                   "suggestion": self.out["suggestion"]},
        }

    # ------------------------------------------------------------------ helpers
    def _reset_output(self):
        self.out = {"ears": "neutral", "halo": "off", "actions": [], "events": [],
                    "notifications": [], "anomaly": None, "suggestion": None}

    def _event(self, name: str, **data):
        e = {"event_id": next(self._ids), "ts": self.now.isoformat(timespec="seconds"),
             "event": name, "mode": self.mode, **data}
        self.events.append(e)
        self.out["events"].append(e)
        return e

    def _act(self, do: str, **data):
        self.out["actions"].append({"do": do, **data})

    def _notify(self, text: str):
        self.out["notifications"].append(f"{self.now.strftime('%H:%M')} {text}")

    def _secs(self, since: Optional[datetime]) -> float:
        return float("inf") if since is None else (self.now - since).total_seconds()

    def _boop_cooling(self) -> bool:
        return self.boop_cooldown_until is not None and self.now < self.boop_cooldown_until

    def _counters(self) -> dict:
        today = self.now.date().isoformat()
        treats = [e for e in self.events if e["event"] == "OUTPUT_CONFIRMED" and e.get("output") == "treat"
                  and e["ts"].startswith(today)]
        hour_ago = (self.now - timedelta(hours=1)).isoformat()
        return {
            "treats_today": len(treats),
            "treats_last_hour": sum(1 for e in treats if e["ts"] >= hour_ago),
            "treats_limit_day": L["treats_per_day"],
            "tug_reps": (self.session or {}).get("reps", 0) if self.mode == "tug" else 0,
            "rolls_session": (self.session or {}).get("rolls", 0) if self.mode == "roll" else 0,
            "toys_tidied_session": (self.session or {}).get("toys", 0) if self.mode == "tidy" else 0,
        }

    def _dog_active(self):
        self.last_dog_activity = self.now

    def _ignore(self, why: str, **data):
        self._event("INPUT_IGNORED", detail=why, **data)

    # ------------------------------------------------------------------ time-based transitions
    def _timeouts(self):
        if self.lockout_until and self.now >= self.lockout_until:
            self.lockout_until = None
            if self.n4["state"] == LOCKOUT:
                self.n4.update(state=PARKED, attachment=None, resistance=0)
                self._event("LOCKOUT_ENDED")
        if self.pending_confirm and self._secs(self.pending_confirm["since"]) > L["request_expiry_s"]:
            self._event("REQUEST_EXPIRED", detail=self.pending_confirm["kind"])
            self.pending_confirm = None
        if self.audio_on_since and self._secs(self.audio_on_since) > L["audio_max_s"]:
            self._audio(False, reason="max duration")
        s = self.session or {}
        if self.mode == "tug" and self.n4["state"] == ACTIVE and self._secs(s.get("start")) > L["tug_session_max_s"]:
            self._to_cooldown("session time limit")
        if self.mode == "roll" and self._secs(s.get("last")) > L["roll_idle_timeout_s"]:
            self._end_session("idle timeout")
        if self.mode == "tidy" and self._secs(s.get("last")) > L["tidy_window_s"]:
            self._end_session("tidy window over")
        self._ml_checks()

    def _ml_checks(self):
        if self._secs(self._anomaly_at) >= 60:   # hourly pattern: checking once a minute is plenty
            self._anomaly_at = self.now
            hour_start = self.now.replace(minute=0, second=0, microsecond=0)
            self._anomaly = self.anomaly.check(ActivityAnomaly.hour_counts(self.events, hour_start))
        self.out["anomaly"] = self._anomaly
        daytime = 8 <= self.now.hour < 21
        if (daytime and self.mode == "idle" and self.last_dog_activity is not None
                and self._secs(self.last_dog_activity) > L["idle_suggest_s"]
                and self._secs(self.suggested_at) > L["idle_suggest_s"]):
            self.suggested_at = self.now
            self.out["suggestion"] = "No dog interaction with the hub for 2 h. Consider offering Tug or Roll Again."

    # ------------------------------------------------------------------ owner commands (from the app)
    def _owner(self, msg: dict):
        action = msg.get("action")
        if action == "offer":
            self._offer(msg.get("feature"))
        elif action == "park":
            self._end_session("owner parked")
        elif action == "stop":
            self._end_session("emergency stop")
            self.device_state = "FAULT"
            self.n4.update(state=FAULT, resistance=0)
            self._act("stop_motors")
            self._event("EMERGENCY_STOP")
            self._notify("Emergency stop pressed. All motors de-energised.")
        elif action == "reset":
            self.device_state = "ONLINE"
            self.n4.update(state=PARKED, attachment=None, resistance=0)
            self.n5 = "IDLE"
            self.pending_output = None
            self._event("FAULT_RESET")
        elif action in ("treats_on", "treats_off"):
            self.treats_enabled = action == "treats_on"
            self._event("SETTING", detail=action)
        elif action in ("greeting_on", "greeting_off"):
            self.greeting_enabled = action == "greeting_on"
            self._event("SETTING", detail=action)
        else:
            self._event("INPUT_REJECTED", detail=f"unknown owner action {action!r}")

    def _offer(self, feature: str):
        if feature not in FEATURES:
            return self._event("INPUT_REJECTED", detail=f"unknown feature {feature!r}")
        if self.device_state != "ONLINE":
            return self._ignore("device not online")
        if self.n4["state"] == LOCKOUT:
            return self._ignore("strap in lockout", feature=feature)
        if self.mode != "idle":
            self._end_session(f"switching to {feature}")
        self.mode = feature
        self.session = {"start": self.now, "last": self.now, "reps": 0, "rolls": 0, "toys": 0}
        if feature in ATTACHMENT_FOR:
            self.n4.update(state=READY, attachment=ATTACHMENT_FOR[feature],
                           resistance=1 if feature == "tug" else 0)
            self._act("extend_strap", node="N4", attachment=ATTACHMENT_FOR[feature])
        self.out["ears"], self.out["halo"] = "small_open", "soft_on"   # availability cue
        self._event("FEATURE_OFFERED", feature=feature)

    def _end_session(self, reason: str):
        if self.mode == "idle":
            return
        self._event("SESSION_ENDED", feature=self.mode, detail=reason)
        if self.n4["state"] in (READY, ACTIVE, COOLDOWN):
            self.n4.update(state=RETRACTING if self.n4["state"] != READY else PARKED, resistance=0)
            if self.n4["state"] == PARKED:
                self.n4["attachment"] = None
                self._act("retract_strap", node="N4")
        self.mode = "idle"
        self.session = None
        self.pending_confirm = None
        self.out["ears"] = "slow_down"

    # ------------------------------------------------------------------ strap pulls (tug, choice)
    def _valid_pull(self, force: float, ms: float) -> bool:
        return force >= self.threshold.value and L["pull_min_ms"] <= ms <= L["pull_max_ms"]

    def _pull(self, msg: dict):
        node = msg.get("node", "N4")
        force, ms = float(msg.get("force", 0)), float(msg.get("duration_ms", 500))
        self._dog_active()
        self._event("PULL_START", node=node, force_peak=force, pull_duration=ms)
        if self._frantic(force):
            return
        if node in CHOICES:
            return self._choice_pull(node, force, ms)
        if node != "N4":
            return self._ignore("not a pull node", node=node)
        if self.mode != "tug" or self.n4["state"] not in (READY, ACTIVE):
            return self._ignore(f"strap {self.n4['state'].lower()} - pull has no effect", node=node)
        if not self._valid_pull(force, ms):
            return self._ignore("below threshold or bad duration", node=node, force_peak=force)
        # valid tug rep (very hard pulls are not used to learn the threshold)
        if force < L["frantic_force_n"]:
            self.threshold.observe(force)
        self.session["reps"] += 1
        self.session["last"] = self.now
        if self.n4["state"] == READY:
            self.n4["state"] = ACTIVE
            self._event("SESSION_STARTED", feature="tug")
        # resistance rises gently every 2 reps, bounded; never linked to availability
        self.n4["resistance"] = min(L["resistance_max"], 1 + self.session["reps"] // 2)
        self._event("PULL_VALID", node="N4", force_peak=force, rep=self.session["reps"])
        self.out["ears"], self.out["halo"] = "rhythm", "rhythm"
        if self.session["reps"] % L["pulls_per_treat"] == 0:
            self._try_treat()

    def _frantic(self, force: float) -> bool:
        if force < L["frantic_force_n"]:
            return False
        window = timedelta(seconds=L["frantic_window_s"])
        self.high_force_pulls = [t for t in self.high_force_pulls if self.now - t <= window] + [self.now]
        if len(self.high_force_pulls) < L["frantic_pulls"] or self.n4["state"] == LOCKOUT:
            return False
        n = len(self.high_force_pulls)
        self.high_force_pulls = []
        self.mode, self.session, self.pending_confirm = "idle", None, None
        self.n4.update(state=LOCKOUT, resistance=0)
        self.lockout_until = self.now + timedelta(seconds=L["lockout_s"])
        self._act("taper_resistance", node="N4")
        self._act("retract_strap_after_release", node="N4")
        self._event("SESSION_LOCKED_OUT", detail=f"{n} high-force pulls within {L['frantic_window_s']} s")
        self._notify(f"{n} high-force pulls occurred within {L['frantic_window_s']} seconds. "
                     f"Strap locked for {L['lockout_s'] // 60} min.")
        self.out["ears"] = "slow_down"
        return True

    def _try_treat(self):
        c = self._counters()
        if not self.treats_enabled:
            why = "treats disabled by owner"
        elif c["treats_today"] >= L["treats_per_day"]:
            why = "daily treat limit reached"
        elif c["treats_last_hour"] >= L["treats_per_hour"]:
            why = "hourly treat limit reached"
        elif self.pending_output or self.n5 != "IDLE":
            why = "output busy or faulted"
        else:
            why = None
        if why:
            self._event("OUTPUT_BLOCKED", output="treat", detail=why)
        else:
            self._request_output("treat", "dispense_treat")
        self._to_cooldown("treat earned" if not why else why)

    def _to_cooldown(self, reason: str):
        self.n4.update(state=COOLDOWN, resistance=0)
        self._act("taper_resistance", node="N4")
        self._event("SESSION_COOLDOWN", detail=reason)
        self.out["ears"] = "one_ear_lift" if reason == "treat earned" else "slow_down"

    def _release(self, msg: dict):
        """Dog let go of the strap. Retraction only happens after release (PRD 9.4.5)."""
        if self.n4["state"] in (COOLDOWN, LOCKOUT) or (self.n4["state"] == RETRACTING):
            self._act("retract_strap", node="N4", speed="slow")
            if self.n4["state"] != LOCKOUT:
                self.n4.update(state=PARKED, attachment=None, resistance=0)
                self._event("PULL_RELEASE", detail="strap retracted")
                if self.mode == "tug":
                    self._end_session("tug round complete")
            else:
                self._event("PULL_RELEASE", detail="strap retracted (lockout)")
        else:
            self._event("PULL_RELEASE")

    # ------------------------------------------------------------------ My Choice
    def _choice_pull(self, slot: str, force: float, ms: float):
        if self.mode != "choice":
            return self._ignore("My Choice not offered", node=slot)
        if self.pending_confirm and self._secs(self.pending_confirm["since"]) < L["choice_window_s"]:
            return self._ignore("choice already made in this window", node=slot)
        if not self._valid_pull(force, ms):
            return self._ignore("below threshold or bad duration", node=slot)
        self.threshold.observe(force)
        meaning = CHOICES[slot]["meaning"]
        self.pending_confirm = {"kind": "choice", "choice": meaning, "slot": slot, "since": self.now}
        self._event("REQUEST_CREATED", request="choice", choice=meaning, node=slot)
        self._notify(f"Dog selected {meaning}. Press N1 to confirm.")
        self._act("light_slot", node=slot)
        self.out["ears"], self.out["halo"] = "one_ear_lift", "success"

    # ------------------------------------------------------------------ boop pad -> walk
    def _boop(self, msg: dict):
        self._dog_active()
        self._event("BOOP", pull_duration=msg.get("duration_ms"))
        if self.mode != "walk":
            return self._ignore("walk not offered (no harness clipped)", node="BOOP")
        if self._boop_cooling() or (self.pending_confirm and self.pending_confirm["kind"] == "walk"):
            return self._ignore("walk request already sent - cooldown", node="BOOP")
        self.pending_confirm = {"kind": "walk", "since": self.now}
        self.boop_cooldown_until = self.now + timedelta(seconds=L["walk_cooldown_s"])
        self._event("REQUEST_CREATED", request="walk", node="BOOP")
        self._notify("Dog requested a walk. Press N1 (Yes) to release the harness.")
        self.out["ears"], self.out["halo"] = "one_ear_lift", "success"

    # ------------------------------------------------------------------ buttons
    def _button(self, msg: dict):
        node = msg.get("node")
        if node == "N2":
            return self._audio(self.audio_on_since is None, reason="dog pressed N2")
        if node != "N1":
            return self._ignore("unknown button", node=node)
        # N1 = owner "Yes": confirm pending request, otherwise start a Tidy cue
        pc = self.pending_confirm
        if pc and pc["kind"] == "walk":
            self._event("HUMAN_CONFIRMED", request="walk", node="N1")
            self.pending_confirm = None
            self._request_output("harness", "release_harness", node="N4")
            self.out["ears"], self.out["halo"] = "wave", "warm_pulse"
        elif pc and pc["kind"] == "choice":
            self._event("HUMAN_CONFIRMED", request="choice", choice=pc["choice"], node="N1",
                        detail=f"owner confirmed {pc['choice']}")
            self._notify(f"Owner confirmed {pc['choice']}.")
            self.pending_confirm = None
            self.out["ears"], self.out["halo"] = "wave", "success"
        elif self.mode == "idle":
            self._offer("tidy")
            self._event("TIDY_CUE", node="N1")
            self._act("play_sound", sound="tidy_cue")
        else:
            self._ignore("nothing to confirm", node="N1")

    def _audio(self, on: bool, reason: str):
        if on:
            self.audio_on_since = self.now
            self._act("audio_start", track="calm_enrichment", max_volume=40)
            self._event("AUDIO_ON", node="N2", detail=reason)
            self.out["ears"], self.out["halo"] = "one_ear_lift", "soft_on"
            self._dog_active()
        else:
            self.audio_on_since = None
            self._act("audio_stop")
            self._event("AUDIO_OFF", node="N2", detail=reason)

    # ------------------------------------------------------------------ Roll Again
    def _ball_in(self, msg: dict):
        self._dog_active()
        self._event("BALL_RETURNED", node="N3")
        if self.mode != "roll":
            return self._ignore("Roll Again not offered", node="N3")
        s = self.session
        if s["rolls"] >= L["rolls_per_session"]:
            self._event("OUTPUT_BLOCKED", output="roll", detail="roll limit for session reached")
            return self._end_session("roll limit reached")
        if self._secs(s.get("last_roll")) < L["roll_gap_s"] or self.pending_output:
            return self._ignore("roll in progress", node="N3")
        s["last"] = s["last_roll"] = self.now
        self._request_output("roll", "roll_ball")
        self.out["ears"] = "wave"

    # ------------------------------------------------------------------ Tidy Together
    def _toy_in_basket(self, msg: dict):
        self._dog_active()
        if self.mode != "tidy":
            return self._ignore("Tidy Together not cued", node="basket")
        self.session["toys"] += 1
        self.session["last"] = self.now
        self._event("TIDY_DEPOSIT", detail=f"toy {self.session['toys']}")
        self._act("play_sound", sound="success")
        self.out["ears"], self.out["halo"] = "wave", "glow"

    # ------------------------------------------------------------------ camera (teammate's AI)
    def _camera(self, msg: dict):
        ev, conf = msg.get("event"), float(msg.get("confidence", 0))
        self._event("CAMERA_EVENT", camera_event=ev, confidence=conf)
        if ev != "HUMAN_DETECTED":
            return
        if not self.greeting_enabled:
            return self._ignore("greeting disabled")
        if conf < L["human_confidence_min"]:
            return self._ignore(f"low confidence {conf:.2f}")
        if self._secs(self.last_greet) < L["greet_cooldown_s"]:
            return self._ignore("already greeted recently")
        self.last_greet = self.now
        self._event("GREETING", detail=f"human detected ({conf:.2f})")
        self._act("ear_wave", repeat=1, speed="slow")
        self._act("halo_pulse", color="warm", repeat=1)
        self.out["ears"], self.out["halo"] = "wave", "warm_pulse"

    # ------------------------------------------------------------------ outputs (N5 spout, N4 harness)
    def _request_output(self, output: str, do: str, node: str = "N5"):
        self.pending_output = {"output": output, "node": node, "since": self.now}
        if node == "N5":
            self.n5 = "BUSY"
        self._act(do, node=node)
        self._event("OUTPUT_REQUESTED", output=output, node=node)

    def _output_confirmed(self, msg: dict):
        po = self.pending_output
        if not po:
            return self._ignore("no output pending")
        self.pending_output = None
        if po["node"] == "N5":
            self.n5 = "IDLE"
        self._event("OUTPUT_CONFIRMED", output=po["output"], node=po["node"])
        if po["output"] == "treat":
            c = self._counters()
            self._notify(f"Dog completed a tug round and got a treat ({c['treats_today']}/{L['treats_per_day']} today).")
        elif po["output"] == "roll":
            self.session and self.session.update(rolls=self.session["rolls"] + 1)
        elif po["output"] == "harness":
            self.n4.update(state=PARKED, attachment=None, resistance=0)
            self._notify("Harness released onto the mat. Enjoy the walk!")
            self._end_session("walk started")

    def _output_failed(self, msg: dict):
        po = self.pending_output
        if not po:
            return self._ignore("no output pending")
        self.pending_output = None
        if po["node"] == "N5":
            self.n5 = "FAULT"          # no automatic retry (PRD 14.3)
        self._event("OUTPUT_FAILED", output=po["output"], node=po["node"], fault_code=msg.get("reason", "jam"))
        self._notify(f"{po['output'].capitalize()} output was requested but not confirmed. Check the device.")
