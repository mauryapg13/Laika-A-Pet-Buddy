"""Render a cartoon 'dog cam' clip with a scripted day, so the pipeline can be tested end to end
without real footage. The script's segments are the ground truth to compare the tracker against.

    python -m laika.camera.synth_video data/videos/synthetic_day.mp4
"""
from __future__ import annotations

import math
import sys

import cv2
import numpy as np

from .config import DEFAULT_ZONES

W, H, FPS = 960, 540, 15
BED, BOWL, DEVICE, DOOR = (0.16, 0.38), (0.14, 0.86), (0.51, 0.90), (0.90, 0.52)

# (behaviour, seconds, target position or None). Positions are the dog's feet, normalized.
SCRIPT = [
    ("sleeping", 50, BED),
    ("walk", 4, BOWL),
    ("eating", 12, BOWL),
    ("walk", 3, DEVICE),
    ("tugging", 15, DEVICE),
    ("zoomies", 10, None),
    ("walk", 4, DOOR),
    ("waiting_at_door", 15, DOOR),
    ("walk", 2, (1.08, 0.52)),
    ("away", 15, (1.08, 0.52)),
    ("walk", 3, (0.60, 0.60)),
    ("walk", 4, BED),
    ("sleeping", 50, BED),
]


def _room() -> np.ndarray:
    img = np.zeros((H, W, 3), np.uint8)
    for y in range(H):  # wall on top, floor below
        img[y] = (190, 205, 215) if y < H * 0.45 else (120 + y // 12, 150 + y // 14, 175 + y // 16)
    z = {k: (int(a * W), int(b * H), int(c * W), int(d * H)) for k, (a, b, c, d) in DEFAULT_ZONES.items()}
    x1, y1, x2, y2 = z["door"]
    cv2.rectangle(img, (x1 + 10, y1 + 5), (x2 - 5, y2), (150, 110, 70), -1)
    cv2.circle(img, (x1 + 25, (y1 + y2) // 2), 5, (40, 180, 220), -1)
    x1, y1, x2, y2 = z["bed"]
    cv2.ellipse(img, ((x1 + x2) // 2, y2 - 25), ((x2 - x1) // 2 - 10, 30), 0, 0, 360, (80, 60, 150), -1)
    cv2.circle(img, (int(BOWL[0] * W) + 50, int(BOWL[1] * H) - 5), 18, (140, 140, 140), -1)
    dx, dy = int(DEVICE[0] * W), int(DEVICE[1] * H)
    cv2.rectangle(img, (dx - 45, dy - 70), (dx + 45, dy - 30), (70, 70, 70), -1)
    for i, col in enumerate([(0, 140, 255), (60, 200, 60), (230, 120, 30)]):  # food / play / outside ropes
        cv2.line(img, (dx - 30 + 30 * i, dy - 30), (dx - 30 + 30 * i, dy + 10), col, 4)
    cv2.putText(img, "DOG CAM 01", (12, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    return img


def _draw_dog(img, fx, fy, t, mode, facing):
    x, y = int(fx * W), int(fy * H)
    lying = mode == "sleeping"
    bw, bh = (70, 26) if lying else (62, 30)
    breathe = int(2 * math.sin(t * 2)) if lying else 0
    body_y = y - bh - (0 if lying else 18)
    fur, dark = (40, 90, 150), (25, 55, 95)
    if not lying:
        for lx in (-40, -18, 18, 40):
            cv2.line(img, (x + lx // 2 * 1, body_y + bh // 2), (x + lx // 2, y), dark, 6)
    cv2.ellipse(img, (x, body_y), (bw // 2 + 10, bh // 2 + breathe), 0, 0, 360, fur, -1)
    wag = math.sin(t * (18 if mode in ("waiting_at_door", "zoomies", "tugging") else 3)) * 0.6
    tail = (x - facing * (bw // 2 + 8), body_y - 4)
    cv2.line(img, tail, (int(tail[0] - facing * 22 * math.cos(wag)), int(tail[1] - 22 * abs(math.sin(wag + 1)))), dark, 5)
    bob = int(6 * math.sin(t * 9)) if mode == "eating" else 0
    head = (x + facing * (bw // 2 + 12), body_y - (0 if lying else 16) + bob + (8 if mode == "eating" else 0))
    cv2.circle(img, head, 17, fur, -1)
    cv2.ellipse(img, (head[0] - facing * 6, head[1] - 8), (6, 12), 20 * facing, 0, 360, dark, -1)
    cv2.circle(img, (head[0] + facing * 14, head[1] + 3), 4, (20, 20, 20), -1)
    if mode == "tugging":  # rope in mouth, pulled taut
        cv2.line(img, (head[0] + facing * 10, head[1] + 5), (int(DEVICE[0] * W), int(DEVICE[1] * H) - 30), (60, 200, 60), 4)


def render(path: str, seed: int = 1):
    rng = np.random.default_rng(seed)
    room = _room()
    writer = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"mp4v"), FPS, (W, H))
    pos = np.array(BED, float)
    facing = 1
    t = 0.0
    for mode, secs, target in SCRIPT:
        n = int(secs * FPS)
        start = pos.copy()
        for i in range(n):
            t += 1 / FPS
            k = (i + 1) / n
            if mode == "walk":
                new = start + (np.array(target) - start) * (k * k * (3 - 2 * k))
            elif mode == "zoomies":  # laps of the room
                a = t * 3.2
                new = np.array([0.5 + 0.33 * math.cos(a), 0.72 + 0.18 * math.sin(a)])
            elif mode == "tugging":  # yank back and forth on the play rope
                new = np.array(target) + np.array([0.03 * math.sin(t * 11) - 0.03, 0.01 * math.sin(t * 7)])
            else:
                new = np.array(target)
            if abs(new[0] - pos[0]) > 1e-3:
                facing = 1 if new[0] > pos[0] else -1
            pos = new
            frame = room.copy()
            if mode != "away":
                _draw_dog(frame, pos[0], pos[1], t, "eating" if mode == "eating" else mode, facing)
            noise = rng.normal(0, 3, frame.shape).astype(np.int16)  # sensor noise
            frame = np.clip(frame.astype(np.int16) + noise, 0, 255).astype(np.uint8)
            writer.write(frame)
    writer.release()
    return t


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "data/videos/synthetic_day.mp4"
    secs = render(out)
    print(f"wrote {out} ({secs:.0f}s). Ground truth:")
    t = 0
    for mode, s, _ in SCRIPT:
        print(f"  {t:6.1f}-{t + s:6.1f}s  {mode}")
        t += s
