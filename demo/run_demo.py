"""Runs the 6 image stories through the device model and prints what the hub does.

    python -m demo.run_demo          # readable story log
    python -m demo.run_demo --json   # also print the full JSON output of every step
Every step's full JSON is saved to demo/demo_output.json (sample data for the web app).
"""
import json
import os
import sys
from datetime import datetime, timedelta

from device_model import Hub

OUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo_output.json")

STORIES = [
    ("1. My Choice (Learn / Choose / Confirm / Go)", [
        ("Owner clips the 3 choice tokens", {"type": "owner", "action": "offer", "feature": "choice"}),
        ("Dog pulls the blue rope (OUTSIDE)", {"type": "pull", "node": "C_LEFT", "force": 4.2, "duration_ms": 700}),
        ("Dog also tugs the yellow ring", {"type": "pull", "node": "C_RIGHT", "force": 4.0, "duration_ms": 600}),
        ("Owner presses N1 (Yes)", {"type": "button", "node": "N1"}),
        ("Owner parks the tokens", {"type": "owner", "action": "park"}),
    ]),
    ("2. Roll Again (Bring / Drop / Roll / Again)", [
        ("Owner offers Roll Again", {"type": "owner", "action": "offer", "feature": "roll"}),
        ("Dog drops ball in the N3 pocket", {"type": "ball_in"}),
        ("N5 spout confirms ball rolled", {"type": "output_confirmed", "node": "N5"}),
        ("Dog brings it back again", {"type": "ball_in"}),
        ("N5 spout confirms ball rolled", {"type": "output_confirmed", "node": "N5"}),
        ("Dog stops playing (3 min pass)", {"type": "tick", "_advance": 180}),
    ]),
    ("3. Tidy Together (Cue / Fetch / Drop / Proud)", [
        ("Owner presses N1 (cue)", {"type": "button", "node": "N1"}),
        ("Dog drops a toy in the basket", {"type": "toy_in_basket"}),
        ("Dog drops another toy", {"type": "toy_in_basket"}),
        ("Window ends (2 min)", {"type": "tick", "_advance": 130}),
    ]),
    ("4. Tug -> Treat (Notice / Pull / Response / Reward)", [
        ("Tug offered to keep the dog active", {"type": "owner", "action": "offer", "feature": "tug"}),
        *[(f"Dog pulls the bone (rep {i})", {"type": "pull", "node": "N4", "force": 4.5 + i * 0.3, "duration_ms": 650})
          for i in range(1, 7)],
        ("Treat sensor confirms drop", {"type": "output_confirmed", "node": "N5"}),
        ("Dog lets go -> strap retracts", {"type": "release", "node": "N4"}),
        ("Dog pulls parked strap very hard", {"type": "pull", "node": "N4", "force": 11.0, "duration_ms": 900}),
    ]),
    ("5. Walk request (Ready / Request / Together / Let's go)", [
        ("Owner clips the harness on N4", {"type": "owner", "action": "offer", "feature": "walk"}),
        ("Dog boops the pad", {"type": "boop", "duration_ms": 300}),
        ("Dog boops again (impatient)", {"type": "boop", "duration_ms": 300}),
        ("Owner presses N1 (Yes)", {"type": "button", "node": "N1"}),
        ("Harness drop confirmed", {"type": "output_confirmed", "node": "N4"}),
    ]),
    ("6. Arrival greeting (Wait / Arrival detected / Greet)", [
        ("Camera: human, low confidence", {"type": "camera", "event": "HUMAN_DETECTED", "confidence": 0.45}),
        ("Camera: human detected", {"type": "camera", "event": "HUMAN_DETECTED", "confidence": 0.93}),
        ("Hub returns to rest", {"type": "tick"}),
    ]),
    ("Extra: N2 audio + safety guard", [
        ("Dog presses N2", {"type": "button", "node": "N2"}),
        ("Dog presses N2 again", {"type": "button", "node": "N2"}),
        ("Tug offered", {"type": "owner", "action": "offer", "feature": "tug"}),
        *[(f"Frantic hard pull {i}", {"type": "pull", "node": "N4", "force": 15, "duration_ms": 400, "_advance": 3})
          for i in range(1, 6)],
    ]),
]


def describe(out: dict) -> str:
    bits = []
    if out["actions"]:
        bits.append("do: " + ", ".join(a["do"] for a in out["actions"]))
    if out["ears"] != "neutral" or out["halo"] != "off":
        bits.append(f"ears={out['ears']} halo={out['halo']}")
    evs = [e["event"] + (f"({e['detail']})" if e.get("detail") else "") for e in out["events"]
           if e["event"] not in ("PULL_START",)]
    if evs:
        bits.append("events: " + ", ".join(evs))
    n4 = out["nodes"]["N4"]
    bits.append(f"N4={n4['state']}")
    return " | ".join(bits)


def main():
    show_json = "--json" in sys.argv
    hub = Hub()
    t = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
    log = []
    for title, steps in STORIES:
        print(f"\n=== {title} ===")
        for label, msg in steps:
            msg = dict(msg)
            t += timedelta(seconds=msg.pop("_advance", 5))
            out = hub.handle({**msg, "ts": t.isoformat()})
            log.append({"story": title, "step": label, "input": msg, "output": out})
            print(f"  {label:36s} -> {describe(out)}")
            for n in out["notifications"]:
                print(f"  {'':36s}    notify: {n}")
            if show_json:
                print(json.dumps(out, indent=2))
    print("\n=== Daily summary (verified events only) ===")
    summary = hub.summary()
    print(json.dumps(summary["counts"], indent=2))
    print(f"ML pull threshold learned: {hub.threshold.value} N")
    with open(OUT_FILE, "w") as f:
        json.dump({"steps": log, "summary": summary}, f, indent=2)
    print("Full JSON of every step saved to demo/demo_output.json")


if __name__ == "__main__":
    main()
