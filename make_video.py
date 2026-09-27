"""Renders a ~35 s explainer video of the device model: python make_video.py -> demo_video.mp4

Left: the hub (button states, ears, halo light, treat/ball drops). Right: input JSON and the model's output.
Uses the real model outputs from the same stories as demo.py.
"""
import json
import math
from datetime import datetime, timedelta

import imageio.v2 as imageio
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Ellipse, FancyBboxPatch

from demo import STORIES
from pawhub import Hub

FPS, HOLD_S, W, H, DPI = 12, 1.45, 12.8, 7.2, 100
KEY_STEPS = {  # steps shown in the video (others still run so state stays correct)
    "Dog pulls the blue rope (OUTSIDE)", "Dog also tugs the yellow ring", "Owner presses N1 (Yes)",
    "Owner offers Roll Again", "Dog drops ball in the N3 pocket",
    "Owner presses N1 (cue)", "Dog drops a toy in the basket",
    "Tug offered to keep the dog active", "Dog pulls the bone (rep 1)", "Dog pulls the bone (rep 6)",
    "Treat sensor confirms drop", "Dog lets go -> strap retracts", "Dog pulls parked strap very hard",
    "Owner clips the harness on N4", "Dog boops the pad", "Dog boops again (impatient)",
    "Harness drop confirmed", "Camera: human, low confidence", "Camera: human detected",
    "Dog presses N2", "Frantic hard pull 5",
}
STATE_COLOR = {"PARKED": "#9ca3af", "IDLE": "#9ca3af", "OFF": "#9ca3af", "READY": "#3b82f6", "ENABLED": "#3b82f6",
               "ACTIVE": "#22c55e", "ON": "#22c55e", "COOLDOWN": "#f59e0b", "BUSY": "#eab308",
               "WAITING_CONFIRM": "#a855f7", "LOCKOUT": "#ef4444", "FAULT": "#ef4444", "RETRACTING": "#f59e0b"}
HALO_COLOR = {"off": None, "soft_on": "#fde68a", "success": "#86efac", "warm_pulse": "#fdba74",
              "glow": "#fef08a", "rhythm": "#93c5fd"}
CREAM, SAGE, OCHRE = "#f5efe3", "#8fa98a", "#d9a441"


def collect():
    hub, t, shots = Hub(), datetime(2026, 9, 27, 10, 0), []
    for title, steps in STORIES:
        for label, msg in steps:
            msg = dict(msg)
            t += timedelta(seconds=msg.pop("_advance", 5))
            out = hub.handle({**msg, "ts": t.isoformat()})
            if label in KEY_STEPS:
                shots.append((title, label, msg, out))
    return shots


def ear_angles(ears: str, k: float):
    wob = math.sin(k * 2 * math.pi * 2)
    return {"wave": (25 * wob, -25 * wob), "rhythm": (10 * wob, 10 * wob), "one_ear_lift": (-35, 0),
            "small_open": (15, -15), "slow_down": (35 * k, -35 * k)}.get(ears, (0, 0))


def draw_hub(ax, out, k):
    ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")
    nodes = out["nodes"]
    la, ra = ear_angles(out["ears"], k)
    for x, ang in ((3.3, la), (6.7, ra)):  # ears
        ax.add_patch(Ellipse((x, 8.9), 1.1, 2.0, angle=ang, color=SAGE, zorder=1))
    ax.add_patch(FancyBboxPatch((2.2, 2.4), 5.6, 6.2, boxstyle="round,pad=0.2,rounding_size=2.2",
                                color=CREAM, ec="#d6cfc0", lw=2, zorder=2))
    for x in (4.3, 5.7):  # eyes (camera)
        ax.add_patch(Ellipse((x, 7.3), 0.28, 0.5, color="#222", zorder=3))
    halo = HALO_COLOR.get(out["halo"])
    if halo:
        a = 0.55 + 0.45 * math.sin(k * math.pi * 4)
        ax.add_patch(Circle((5, 5.2), 1.75, color=halo, alpha=a, zorder=3))
    ax.add_patch(Circle((5, 5.2), 1.45, color=SAGE, zorder=4))
    ax.text(5, 5.2, "BOOP", ha="center", va="center", color="white", fontsize=11, weight="bold", zorder=5)
    ring(ax, 5, 5.2, 1.52, nodes["BOOP"]["state"], lw=3)

    spots = {"N1": (2.9, 7.6, OCHRE), "N2": (7.1, 7.6, CREAM), "N3": (2.35, 5.2, "white"),
             "N5": (3.0, 3.1, OCHRE), "N4": (7.0, 3.1, CREAM)}
    for n, (x, y, fill) in spots.items():
        ax.add_patch(Circle((x, y), 0.42, color=fill, ec="#bbb", zorder=5))
        ring(ax, x, y, 0.5, nodes[n]["state"], lw=4)
        ax.text(x, y, n, ha="center", va="center", fontsize=9, weight="bold", zorder=7)
    ax.text(1.0, 7.6, "owner\nYes", ha="center", va="center", fontsize=8, color="#555")
    ax.text(9.0, 7.6, "audio", ha="center", va="center", fontsize=8, color="#555")
    ax.text(1.0, 5.2, "ball\npocket", ha="center", va="center", fontsize=8, color="#555")
    ax.text(1.4, 3.1, "treat/ball\nspout", ha="center", va="center", fontsize=8, color="#555")

    n4 = nodes["N4"]
    if n4["state"] not in ("PARKED",):  # strap hanging out
        length = 1.6 if n4["state"] in ("ACTIVE",) else 1.2
        ax.plot([7.0, 7.0], [2.7, 2.7 - length], color="#556b55", lw=6, zorder=4)
        att = {"bone_tug": "bone", "harness": "harness", "choice_tokens": "tokens"}.get(n4["attachment"], "")
        ax.text(7.0, 2.4 - length, att, ha="center", va="top", fontsize=9,
                bbox=dict(boxstyle="round", fc="#e7dcc8", ec="#b9a98a"), zorder=6)
    if out["choice_slots"]:
        for i, (slot, v) in enumerate(out["choice_slots"].items()):
            x = 2.4 + i * 1.3
            ax.add_patch(Circle((x, 1.2), 0.45, color="#fde047" if v["light"] else "#e5e7eb", ec="#999", zorder=5))
            ax.text(x, 1.2, v["meaning"], ha="center", va="center", fontsize=7, zorder=6)
    dos = [a["do"] for a in out["actions"]]
    if "dispense_treat" in dos:
        ax.add_patch(Circle((3.0, 2.5 - 1.8 * k), 0.15, color="#7c4a1e", zorder=6))
    if "roll_ball" in dos:
        ax.add_patch(Circle((3.0 - 2.0 * k, 1.2), 0.3, color="#e8a33d", zorder=6))
    if "release_harness" in dos:
        ax.text(7.0, 0.5, "harness drops to mat", ha="center", fontsize=9, color="#555")
    if "audio_start" in dos:
        ax.text(8.2, 8.4, "♪ ♫", fontsize=18, color="#6b8f6b", alpha=0.5 + 0.5 * k)
    if out["device_state"] == "FAULT":
        ax.text(5, 9.9, "FAULT", ha="center", color="red", weight="bold")


def ring(ax, x, y, r, state, lw):
    ax.add_patch(Circle((x, y), r, fill=False, ec=STATE_COLOR.get(state, "#9ca3af"), lw=lw, zorder=6))


def draw_panel(ax, title, label, msg, out):
    ax.axis("off"); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.text(0, 0.97, title, fontsize=15, weight="bold", va="top", color="#1f2937")
    ax.text(0, 0.89, "What happens:  " + label, fontsize=12, va="top", color="#374151")
    ax.text(0, 0.81, "INPUT JSON", fontsize=9, weight="bold", color="#2563eb", va="top")
    ax.text(0, 0.77, wrap(json.dumps(msg), 70), fontsize=9.5, family="monospace", va="top",
            bbox=dict(boxstyle="round", fc="#eff6ff", ec="#bfdbfe"))
    n4 = out["nodes"]["N4"]
    evs = [e["event"] + (f" ({e['detail']})" if e.get("detail") else "") for e in out["events"]
           if e["event"] != "PULL_START"]
    rows = [
        ("mode", out["mode"]),
        ("actions (hardware)", ", ".join(a["do"] for a in out["actions"]) or "-  (nothing moves)"),
        ("ears / halo", f"{out['ears']} / {out['halo']}"),
        ("N4 strap", f"{n4['state']}  {n4['attachment'] or ''}"),
        ("events", wrap("; ".join(evs) or "-", 52)),
        ("counters", f"treats today {out['counters']['treats_today']}/8 · tug reps {out['counters']['tug_reps']}"
                     f" · rolls {out['counters']['rolls_session']}"),
        ("ml", f"pull threshold {out['ml']['pull_threshold_n']} N"),
    ]
    ax.text(0, 0.64, "OUTPUT JSON (key fields)", fontsize=9, weight="bold", color="#16a34a", va="top")
    y = 0.59
    for k, v in rows:
        ax.text(0, y, k, fontsize=9.5, weight="bold", va="top", color="#374151")
        ax.text(0.33, y, v, fontsize=9.5, family="monospace", va="top", color="#111")
        y -= 0.058 * (1 + v.count("\n"))
    if out["notifications"]:
        ax.text(0, 0.1, "Owner notification:  " + wrap(out["notifications"][0][6:], 60), fontsize=10.5,
                va="top", color="#7c2d12", bbox=dict(boxstyle="round", fc="#fff7ed", ec="#fdba74"))


def wrap(s, n):
    out, line = [], ""
    for word in s.split(" "):
        if len(line) + len(word) > n:
            out.append(line); line = ""
        line += word + " "
    return "\n".join(out + [line.rstrip()])


def legend(fig):
    x = 0.02
    for name, c in (("parked/idle", "#9ca3af"), ("ready", "#3b82f6"), ("active/on", "#22c55e"),
                    ("cooldown", "#f59e0b"), ("waiting owner", "#a855f7"), ("lockout/fault", "#ef4444")):
        fig.text(x, 0.02, "●", color=c, fontsize=14); fig.text(x + 0.018, 0.024, name, fontsize=9)
        x += 0.105


def render(fig) -> "np.ndarray":
    fig.canvas.draw()
    return np.asarray(fig.canvas.buffer_rgba())[:, :, :3].copy()


import numpy as np  # noqa: E402


def title_card(writer, text, sub, seconds):
    fig = plt.figure(figsize=(W, H), dpi=DPI, facecolor="#faf7f0")
    fig.text(0.5, 0.58, text, ha="center", fontsize=34, weight="bold", color="#3f5a3c")
    fig.text(0.5, 0.45, sub, ha="center", fontsize=15, color="#444")
    frame = render(fig); plt.close(fig)
    for _ in range(int(seconds * FPS)):
        writer.append_data(frame)


def main():
    shots = collect()
    writer = imageio.get_writer("demo_video.mp4", fps=FPS, codec="libx264", quality=8, macro_block_size=8)
    title_card(writer, "PawHub device model", "Every event goes in as JSON  →  the model returns the hub's full state as JSON", 2.5)
    n = int(HOLD_S * FPS)
    for title, label, msg, out in shots:
        for f in range(n):
            fig = plt.figure(figsize=(W, H), dpi=DPI, facecolor="#faf7f0")
            draw_hub(fig.add_axes([0.0, 0.06, 0.42, 0.92]), out, f / n)
            draw_panel(fig.add_axes([0.44, 0.06, 0.54, 0.9]), title, label, msg, out)
            legend(fig)
            writer.append_data(render(fig)); plt.close(fig)
    title_card(writer, "Harder pulls never win.", "Treats only count when confirmed  ·  harness needs the owner  ·  frantic pulls → lockout", 2.5)
    writer.close()
    print(f"demo_video.mp4 written: {len(shots)} steps, ~{2.5 * 2 + len(shots) * HOLD_S:.0f} s")


if __name__ == "__main__":
    main()
