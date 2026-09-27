"""Small ML helpers. They personalise and summarise; they never control force, treats or release."""
from collections import Counter
from datetime import datetime
from typing import List, Optional

import numpy as np
from sklearn.ensemble import IsolationForest


class ThresholdLearner:
    """Learns the dog's valid-pull threshold from its own successful pulls, clamped to safe bounds."""

    def __init__(self, default: float, bounds: tuple, min_samples: int = 5, window: int = 50):
        self.default, self.lo, self.hi = default, bounds[0], bounds[1]
        self.min_samples, self.window = min_samples, window
        self.forces: List[float] = []

    def observe(self, force: float):
        self.forces = (self.forces + [force])[-self.window:]

    @property
    def value(self) -> float:
        if len(self.forces) < self.min_samples:
            return self.default
        learned = 0.8 * float(np.percentile(self.forces, 30))
        return round(min(self.hi, max(self.lo, learned)), 2)


ACTIVITY_KEYS = ["boops", "pulls", "treats", "rolls", "tidy", "ignored"]
_EVENT_TO_KEY = {"BOOP": "boops", "PULL_VALID": "pulls", "OUTPUT_CONFIRMED_TREAT": "treats",
                 "OUTPUT_CONFIRMED_ROLL": "rolls", "TIDY_DEPOSIT": "tidy", "INPUT_IGNORED": "ignored"}
# typical per-hour rates for a normal day (daytime hours), used to simulate training data
_NORMAL_RATES = {"boops": 0.6, "pulls": 4.0, "treats": 0.5, "rolls": 1.5, "tidy": 0.4, "ignored": 0.8}


class ActivityAnomaly:
    """Isolation Forest on hourly interaction counts. Output is a factual sentence, never an emotion."""

    def __init__(self, seed: int = 0, hours: int = 3000):
        rng = np.random.default_rng(seed)
        lam = np.array([_NORMAL_RATES[k] for k in ACTIVITY_KEYS])
        X = rng.poisson(lam * rng.uniform(0.3, 1.7, size=(hours, 1)), size=(hours, len(lam)))
        self.mean = X.mean(axis=0)
        self.model = IsolationForest(n_estimators=150, contamination=0.02, random_state=seed).fit(X)

    @staticmethod
    def hour_counts(events: List[dict], hour_start: datetime) -> dict:
        counts = Counter()
        for e in events:
            ts = datetime.fromisoformat(e["ts"])
            if ts >= hour_start and (ts - hour_start).total_seconds() < 3600:
                key = e["event"]
                if key == "OUTPUT_CONFIRMED":
                    key += "_" + e.get("output", "").upper()
                if key in _EVENT_TO_KEY:
                    counts[_EVENT_TO_KEY[key]] += 1
        return {k: counts.get(k, 0) for k in ACTIVITY_KEYS}

    def check(self, counts: dict) -> Optional[str]:
        x = np.array([[counts[k] for k in ACTIVITY_KEYS]])
        if self.model.predict(x)[0] != -1:
            return None
        high = [f"{k} {counts[k]} (normal ~{self.mean[i]:.1f})" for i, k in enumerate(ACTIVITY_KEYS)
                if counts[k] > 2 * self.mean[i] + 2]
        return "Unusual hour: " + (", ".join(high) if high else "interaction pattern differs from normal")


def daily_summary(events: List[dict], day: str) -> dict:
    """Built only from recorded events. Camera events keep their confidence label."""
    todays = [e for e in events if e["ts"].startswith(day)]
    c = Counter(e["event"] for e in todays)
    confirmed = Counter(e.get("output") for e in todays if e["event"] == "OUTPUT_CONFIRMED")
    timeline_events = {"REQUEST_CREATED", "HUMAN_CONFIRMED", "OUTPUT_CONFIRMED", "OUTPUT_FAILED",
                       "SESSION_STARTED", "SESSION_ENDED", "SESSION_LOCKED_OUT", "GREETING",
                       "TIDY_DEPOSIT", "AUDIO_ON", "AUDIO_OFF", "EMERGENCY_STOP"}
    return {
        "day": day,
        "counts": {
            "boops": c["BOOP"], "valid_pulls": c["PULL_VALID"], "ignored_inputs": c["INPUT_IGNORED"],
            "treats_confirmed": confirmed["treat"], "balls_rolled": confirmed["roll"],
            "harness_releases": confirmed["harness"], "requests": c["REQUEST_CREATED"],
            "toys_tidied": c["TIDY_DEPOSIT"], "greetings": c["GREETING"], "lockouts": c["SESSION_LOCKED_OUT"],
            "output_failures": c["OUTPUT_FAILED"],
        },
        "timeline": [{"time": e["ts"][11:16], "event": e["event"], "detail": e.get("detail", "")}
                     for e in todays if e["event"] in timeline_events],
        "camera": [{"time": e["ts"][11:16], "event": e.get("camera_event"), "confidence": e.get("confidence")}
                   for e in todays if e["event"] == "CAMERA_EVENT"],
    }
