"""Class-gated static landmark association with observation provenance."""
from dataclasses import asdict
from copy import deepcopy

import numpy as np

from .semantic_geometry import SemanticConfig, localize_detections


class SemanticMap:
    def __init__(self, config=None):
        self.config = config or SemanticConfig()
        self.landmarks, self.next_id, self.seen_frames = {}, 1, set()

    def update(self, frame, detections, pose, filename):
        key = (frame.timestamp_domain, frame.number, frame.timestamp_ms)
        if key in self.seen_frames:
            raise ValueError("Semantic observations already processed for this frame identity")
        observations, rejected = localize_detections(frame, detections, pose, self.config)
        self.seen_frames.add(key)
        pairs = []
        for index, observation in enumerate(observations):
            for object_id, landmark in self.landmarks.items():
                distance = float(np.linalg.norm(np.array(observation["xyz_world_m"])-landmark["mean"]))
                if observation["label"] == landmark["label"] and distance <= self.config.association_m:
                    pairs.append((distance, object_id, index))
        matched, used = {}, set()
        for _, object_id, index in sorted(pairs):
            if index not in matched and object_id not in used:
                matched[index] = object_id
                used.add(object_id)
        records = []
        for index, observation in enumerate(observations):
            object_id = matched.get(index)
            if object_id is None:
                if len(self.landmarks) >= self.config.max_landmarks:
                    rejected.append({"detection_index": observation["detection_index"], "reason": "landmark_capacity"})
                    continue
                object_id = f"object-{self.next_id:06d}"
                self.next_id += 1
                self.landmarks[object_id] = {"label": observation["label"], "count": 0,
                    "mean": np.zeros(3), "m2": np.zeros((3, 3)), "confidence_sum": 0.,
                    "low": np.full(3, np.inf), "high": np.full(3, -np.inf), "history": []}
            record = dict(observation, object_id=object_id, file=filename,
                          frame_number=frame.number, timestamp_ms=frame.timestamp_ms,
                          timestamp_domain=frame.timestamp_domain, camera_to_world=np.asarray(pose).tolist())
            landmark = self.landmarks[object_id]
            self._accumulate(landmark, record)
            record["object_xyz_world_m"] = landmark["mean"].tolist()
            record["object_status"] = self._status(landmark)
            records.append(record)
        return {"observations": records, "rejected": rejected}

    def _status(self, landmark):
        return "confirmed" if landmark["count"] >= self.config.min_observations else "tentative"

    def _accumulate(self, landmark, record):
        position = np.array(record["xyz_world_m"])
        landmark["count"] += 1
        delta = position-landmark["mean"]
        landmark["mean"] += delta/landmark["count"]
        landmark["m2"] += np.outer(delta, position-landmark["mean"])
        landmark["confidence_sum"] += record["confidence"]
        landmark["low"] = np.minimum(landmark["low"], record["visible_min_world_m"])
        landmark["high"] = np.maximum(landmark["high"], record["visible_max_world_m"])
        identity = {key: record[key] for key in ("file", "frame_number", "timestamp_ms", "timestamp_domain")}
        if landmark["count"] == 1:
            landmark["first_seen"] = identity
        landmark["last_seen"] = identity
        landmark["history"].append(dict(record))
        del landmark["history"][:-self.config.history_limit]

    def report(self):
        objects = []
        for object_id, landmark in sorted(self.landmarks.items()):
            count = landmark["count"]
            objects.append({"object_id": object_id, "label": landmark["label"], "status": self._status(landmark),
                "xyz_world_m": landmark["mean"].tolist(), "observation_count": count,
                "mean_detection_confidence": landmark["confidence_sum"]/count,
                "position_scatter_m2": (landmark["m2"]/max(1, count-1)).tolist(),
                "visible_min_world_m": landmark["low"].tolist(), "visible_max_world_m": landmark["high"].tolist(),
                "visible_extent_world_m": (landmark["high"]-landmark["low"]).tolist(),
                "first_seen": dict(landmark["first_seen"]), "last_seen": dict(landmark["last_seen"]),
                "recent_observations": deepcopy(landmark["history"])})
        return {"semantic_schema": 1, "coordinate_system": "world = first camera optical frame; meters",
                "settings": asdict(self.config), "objects": objects,
                "limits": "Static-landmark hypothesis; visible surfaces, local odometry drift, no cross-session identity. Scatter is not calibrated uncertainty."}


def query_objects(report, label=None, minimum=1, confirmed_only=False):
    if not isinstance(report, dict) or report.get("semantic_schema") != 1 or not isinstance(report.get("objects"), list):
        raise ValueError("Expected semantic_schema=1 object map")
    if type(minimum) is not int or minimum < 1:
        raise ValueError("Minimum observations must be a positive integer")
    selected = []
    for obj in report["objects"]:
        if not isinstance(obj, dict) or not isinstance(obj.get("label"), str) or type(obj.get("observation_count")) is not int:
            raise ValueError("Invalid semantic object record")
        if label is not None and obj["label"].casefold() != label.casefold():
            continue
        if obj["observation_count"] < minimum or (confirmed_only and obj.get("status") != "confirmed"):
            continue
        selected.append(obj)
    return selected
