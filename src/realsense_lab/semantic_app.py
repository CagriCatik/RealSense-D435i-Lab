"""Semantic-session adapter: journaling, export and detector selection."""
from contextlib import ExitStack
import csv
import json
from pathlib import Path

import numpy as np

from .semantic_geometry import SemanticConfig
from .semantic_map import SemanticMap
from .semantic_sources import frame_fingerprint
from .storage import write_json, write_ply


class SemanticSession:
    def __init__(self, detector, config=None):
        self.detector, self.map = detector, SemanticMap(config)
        self.output, self.stack = None, None
        self.rejected, self.total = {}, 0

    def start(self, output):
        self.output = Path(output)
        self.stack = ExitStack()
        try:
            self.raw = self.stack.enter_context((self.output/"detections.jsonl").open("x", encoding="utf-8"))
            self.observations = self.stack.enter_context((self.output/"observations.jsonl").open("x", encoding="utf-8"))
        except Exception:
            self.close()
            raise

    def process(self, frame, tracking, filename):
        identity = {"file": filename, "frame_number": frame.number, "timestamp_ms": frame.timestamp_ms,
                    "timestamp_domain": frame.timestamp_domain}
        pose = tracking["camera_to_world"]
        detections = self.detector.predict(frame) if pose is not None else []
        raw = dict(identity, detection_schema=1, detections=detections,
                   frame_sha256=frame_fingerprint(frame),
                   detector=getattr(self.detector, "metadata", {"backend": "custom"}),
                   inference_skipped=pose is None)
        self.raw.write(json.dumps(raw, allow_nan=False)+"\n")
        self.raw.flush()
        if pose is None:
            result = {"observations": [], "rejected": [{"reason": "pose_unavailable"}]}
        else:
            result = self.map.update(frame, detections, pose, filename)
        self.total += len(result["observations"])
        for item in result["rejected"]:
            self.rejected[item["reason"]] = self.rejected.get(item["reason"], 0)+1
        self.observations.write(json.dumps(dict(identity, observation_schema=1, **result), allow_nan=False)+"\n")
        self.observations.flush()
        return result

    def finish(self, tracking_status):
        report = self.map.report()
        report.update(mapping_status=tracking_status, detector=getattr(self.detector, "metadata", {"backend": "custom"}),
                      accepted_observations=self.total, rejected_reasons=self.rejected)
        write_json(self.output/"semantic_map.json", report)
        objects = report["objects"]
        points = np.array([obj["xyz_world_m"] for obj in objects], dtype=float).reshape(-1, 3)
        colors = np.array([(70, 210, 180) if obj["status"] == "confirmed" else (240, 180, 60)
                           for obj in objects], np.uint8).reshape(-1, 3)
        write_ply(self.output/"objects.ply", points, colors)
        with (self.output/"objects.csv").open("x", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(["object_id", "label", "status", "observations", "x_m", "y_m", "z_m", "mean_confidence"])
            for obj in objects:
                writer.writerow([obj["object_id"], obj["label"], obj["status"], obj["observation_count"],
                                 *obj["xyz_world_m"], obj["mean_detection_confidence"]])
        return {"landmarks": len(objects), "confirmed": sum(obj["status"] == "confirmed" for obj in objects),
                "observations": self.total, "rejected_reasons": dict(self.rejected)}

    def close(self):
        if self.stack is not None:
            self.stack.close()


def make_semantic_session(args):
    config = SemanticConfig.load(args.semantic_config)
    if args.weights:
        from .detection import Detector
        detector = Detector(args.weights, confidence=config.confidence)
    else:
        from .semantic_sources import DemoDetector, RecordedDetector
        journal = args.detections
        if journal is None and args.source == "replay" and args.input:
            candidate = Path(args.input)
            candidate = (candidate if candidate.is_dir() else candidate.parent)/"detections.jsonl"
            if candidate.is_file():
                journal = candidate
        if journal:
            detector = RecordedDetector(journal)
        elif args.source == "demo" and args.demo_scene in (None, "room"):
            detector = DemoDetector()
        else:
            raise ValueError("Semantic mapping needs local --weights or --detections; fixture only works with the room demo")
    return SemanticSession(detector, config)
