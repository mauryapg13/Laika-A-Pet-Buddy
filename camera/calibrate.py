"""Draw the configured zones and a 10% grid over a frame of your footage, to help set DEFAULT_ZONES.

    python -m camera.calibrate data/videos/my_dog.mp4 [seconds_in]
"""
import sys

import cv2

from .config import DEFAULT_ZONES


def main():
    path = sys.argv[1]
    at = float(sys.argv[2]) if len(sys.argv) > 2 else 0
    cap = cv2.VideoCapture(path)
    cap.set(cv2.CAP_PROP_POS_MSEC, at * 1000)
    ok, frame = cap.read()
    if not ok:
        sys.exit(f"could not read a frame from {path}")
    h, w = frame.shape[:2]
    for i in range(1, 10):
        cv2.line(frame, (w * i // 10, 0), (w * i // 10, h), (255, 255, 255), 1)
        cv2.line(frame, (0, h * i // 10), (w, h * i // 10), (255, 255, 255), 1)
        cv2.putText(frame, f"{i / 10:.1f}", (w * i // 10 + 2, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        cv2.putText(frame, f"{i / 10:.1f}", (2, h * i // 10 - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
    for name, (x1, y1, x2, y2) in DEFAULT_ZONES.items():
        cv2.rectangle(frame, (int(x1 * w), int(y1 * h)), (int(x2 * w), int(y2 * h)), (0, 200, 255), 2)
        cv2.putText(frame, name, (int(x1 * w) + 4, int(y1 * h) + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 255), 2)
    out = "out/calibration.jpg"
    cv2.imwrite(out, frame)
    print(f"wrote {out}. Adjust DEFAULT_ZONES in camera/config.py (or write <video>.zones.json) so each box covers where the dog's feet go.")


if __name__ == "__main__":
    main()
