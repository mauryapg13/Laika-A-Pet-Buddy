"""Tunable camera settings: zones and motion thresholds. (Hub rules live in device_model/config.py.)"""
from dataclasses import dataclass, field

# Zones are normalized (x1, y1, x2, y2) rectangles in the camera frame, 0..1.
# Calibrate these once per camera placement: `python -m camera.calibrate <video>`.
DEFAULT_ZONES = {
    "food_bowl": (0.02, 0.62, 0.25, 0.98),
    "door": (0.80, 0.05, 0.99, 0.60),
    "tug_device": (0.40, 0.70, 0.62, 0.99),   # where the Laika hub's strap is
    "bed": (0.02, 0.05, 0.30, 0.45),
}


@dataclass
class VisionConfig:
    sample_fps: float = 2.0          # frames analysed per second of video (snapshots, not every frame)
    use_detector: bool = True        # YOLO dog detector if models/yolo11n.onnx exists; else motion only
    work_width: int = 480            # frames are downscaled to this width before processing
    min_blob_frac: float = 0.004     # smallest foreground blob (fraction of frame) that counts as the dog
    # Speeds are in dog body-lengths per second, so they hold for close-ups and wide shots alike.
    zoomies_speed: float = 2.5
    walking_speed: float = 0.35
    # Fraction of the dog's box that changed between snapshots: high = wiggling/tugging in place.
    active_motion: float = 0.18
    still_motion: float = 0.03
    sleep_after_s: float = 45.0      # resting this long in a row becomes "sleeping"
    smooth_window: int = 5           # majority-vote window over per-snapshot labels
    min_episode_s: float = 3.0       # shorter episodes are merged into neighbours
    zones: dict = field(default_factory=lambda: dict(DEFAULT_ZONES))
