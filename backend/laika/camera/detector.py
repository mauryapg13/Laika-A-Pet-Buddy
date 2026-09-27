"""Dog detector: YOLO11n (COCO) run through OpenCV's DNN module, so no torch/ultralytics install.

Model: models/yolo11n.onnx from github.com/ultralytics/assets (AGPL-3.0).
"""
from __future__ import annotations

import os
from pathlib import Path

import cv2
import numpy as np

from laika import REPO_ROOT

def model_path() -> Path:
    """models/yolo11n.onnx at the repo root, or LAIKA_DETECTOR_MODEL=/path/to/model.onnx (checked at use time, after .env)."""
    return Path(os.environ.get("LAIKA_DETECTOR_MODEL") or REPO_ROOT / "models" / "yolo11n.onnx")
# COCO ids. Small/curled-up dogs are regularly scored as "cat", so both count as the dog.
PERSON, DOG, CAT = 0, 16, 15
INPUT = 640


class DogDetector:
    def __init__(self, path: str | Path | None = None, min_score: float = 0.35):
        self.net = cv2.dnn.readNetFromONNX(str(path or model_path()))
        self.min_score = min_score

    @classmethod
    def available(cls) -> bool:
        return model_path().exists()

    def detect(self, frame: np.ndarray):
        """Returns (dogs, people): each [(x1, y1, x2, y2, score)] normalized to the frame, best first."""
        h, w = frame.shape[:2]
        # Letterbox to a 640 square so portrait phone video isn't squashed.
        scale = INPUT / max(h, w)
        nh, nw = round(h * scale), round(w * scale)
        canvas = np.full((INPUT, INPUT, 3), 114, np.uint8)
        canvas[:nh, :nw] = cv2.resize(frame, (nw, nh))
        self.net.setInput(cv2.dnn.blobFromImage(canvas, 1 / 255, (INPUT, INPUT), swapRB=True))
        out = self.net.forward()[0].T                    # (8400, 84): cx, cy, bw, bh, 80 class scores
        dogs = self._boxes(out, np.maximum(out[:, 4 + DOG], out[:, 4 + CAT]), scale, w, h)
        people = self._boxes(out, out[:, 4 + PERSON], scale, w, h)
        return dogs, people

    def _boxes(self, out, scores, scale, w, h):
        keep = scores >= self.min_score
        if not keep.any():
            return []
        cx, cy, bw, bh = (out[keep, i] / scale for i in range(4))
        boxes = np.stack([cx - bw / 2, cy - bh / 2, bw, bh], 1)
        idx = cv2.dnn.NMSBoxes(boxes.tolist(), scores[keep].tolist(), self.min_score, 0.45)
        dets = []
        for i in np.array(idx).flatten():
            x, y, bw_, bh_ = boxes[i]
            dets.append((max(0.0, x / w), max(0.0, y / h), min(1.0, (x + bw_) / w), min(1.0, (y + bh_) / h),
                         float(scores[keep][i])))
        return sorted(dets, key=lambda d: -d[4])


def _iou(a, b) -> float:
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union > 0 else 0.0


def drop_person_lookalikes(dogs: list, people: list) -> list:
    """A 'dog'/'cat' box sitting on the same spot as a more confident person box is the person."""
    return [d for d in dogs if not any(_iou(d, p) > 0.6 and p[4] >= d[4] for p in people)]


def mask_out_people(mask: np.ndarray, people: list, pad: float = 0.03) -> None:
    """Zero the motion mask where people are, so a moving human can't become 'the dog'."""
    h, w = mask.shape[:2]
    for x1, y1, x2, y2, _ in people:
        mask[max(0, int((y1 - pad) * h)):int((y2 + pad) * h), max(0, int((x1 - pad) * w)):int((x2 + pad) * w)] = 0
