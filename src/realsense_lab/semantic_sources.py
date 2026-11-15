"""Synthetic color fixture and strict recorded-detection replay adapters."""
from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
from pathlib import Path

import numpy as np


def frame_key(frame):
    return frame.timestamp_domain, frame.number, frame.timestamp_ms


def frame_fingerprint(frame):
    digest = hashlib.sha256(json.dumps(asdict(frame.intrinsics), sort_keys=True).encode())
    for array in (frame.color, frame.depth_m, frame.rays):
        if array is not None:
            digest.update(str(array.dtype).encode())
            digest.update(np.ascontiguousarray(array).tobytes())
    return digest.hexdigest()


class DemoDetector:
    metadata = {"backend": "synthetic_color_fixture", "learned_model": False,
                "description": "Known room-demo colors only; not real-world object recognition"}

    def predict(self, frame):
        r, g, b = [frame.color[..., i] for i in range(3)]
        masks = (("demo_crate", (r >= 190) & (g >= 120) & (g < 190) & (b < 90)),
                 ("demo_cabinet", (r < 140) & (g >= 160) & (b >= 90) & (b < 150)))
        detections = []
        for label, mask in masks:
            y, x = np.nonzero(mask)
            if len(x):
                detections.append({"label": label, "confidence": 1.,
                    "xyxy": [int(x.min()), int(y.min()), int(x.max()+1), int(y.max()+1)]})
        return detections


class RecordedDetector:
    def __init__(self, path):
        self.records = {}
        self.metadata = {"backend": "recorded_detections", "source_file": Path(path).name}
        with Path(path).open(encoding="utf-8") as stream:
            for line in stream:
                item = json.loads(line)
                if not isinstance(item, dict) or item.get("detection_schema") != 1 or not isinstance(item.get("detections"), list):
                    raise ValueError("Detection journal requires detection_schema=1 and a detections list")
                if (not isinstance(item.get("timestamp_domain"), str) or type(item.get("frame_number")) is not int
                        or type(item.get("timestamp_ms")) not in (int, float) or not np.isfinite(item["timestamp_ms"])):
                    raise ValueError("Detection journal needs exact finite frame identity")
                key = item["timestamp_domain"], item["frame_number"], item["timestamp_ms"]
                fingerprint = item.get("frame_sha256")
                if not isinstance(fingerprint, str) or len(fingerprint) != 64 or any(c not in "0123456789abcdef" for c in fingerprint):
                    raise ValueError("Detection journal needs a SHA256 frame fingerprint")
                if key in self.records:
                    raise ValueError("Duplicate frame identity in detection journal")
                self.records[key] = item

    def predict(self, frame):
        if frame_key(frame) not in self.records:
            raise ValueError("No recorded detections for this exact frame identity")
        item = self.records[frame_key(frame)]
        if item.get("inference_skipped"):
            raise ValueError("Original inference was skipped; run a detector for this newly accepted frame")
        if item["frame_sha256"] != frame_fingerprint(frame):
            raise ValueError("Recorded detections do not match the current RGB-D frame contents")
        return deepcopy(item["detections"])
