"""Greedy metric centroid association; educational, not a re-identification model."""
from dataclasses import dataclass

import numpy as np


@dataclass
class Track:
    id: int
    label: str
    xyz: np.ndarray
    timestamp_ms: float
    velocity: np.ndarray | None = None
    missed: int = 0


class Tracker:
    def __init__(self, gate_m=.5, max_missed=10):
        if not np.isfinite(gate_m) or gate_m <= 0 or max_missed < 0:
            raise ValueError("Invalid tracking parameters")
        self.gate_m, self.max_missed = gate_m, max_missed
        self.tracks, self.next_id, self.last_timestamp = {}, 1, None

    def update(self, detections, timestamp_ms):
        if not np.isfinite(timestamp_ms):
            raise ValueError("Finite tracking timestamp required")
        if self.last_timestamp is not None and timestamp_ms <= self.last_timestamp:
            self.tracks.clear()  # playback restart or clock reset; never divide by <=0 dt
        self.last_timestamp = timestamp_ms
        for track in self.tracks.values():
            track.missed += 1
        candidates = []
        for index, item in enumerate(detections):
            item.pop("track_id", None)
            item.pop("velocity_m_s", None)
            if item.get("xyz_m") is None:
                continue
            xyz = np.asarray(item["xyz_m"], dtype=float)
            if xyz.shape != (3,) or not np.isfinite(xyz).all():
                raise ValueError("Detection XYZ must be finite")
            for track in self.tracks.values():
                distance = float(np.linalg.norm(xyz-track.xyz))
                if track.label == item["label"] and distance <= self.gate_m:
                    candidates.append((distance, track.id, index))
        assigned_tracks, assigned_items = set(), set()
        for _, track_id, index in sorted(candidates):
            if track_id in assigned_tracks or index in assigned_items:
                continue
            item, track = detections[index], self.tracks[track_id]
            xyz = np.array(item["xyz_m"])
            dt = (timestamp_ms-track.timestamp_ms)/1000
            track.velocity = (xyz-track.xyz)/dt if dt > 0 else None
            track.xyz, track.timestamp_ms, track.missed = xyz, timestamp_ms, 0
            assigned_tracks.add(track_id)
            assigned_items.add(index)
            item["track_id"] = track_id
            item["velocity_m_s"] = track.velocity.tolist() if track.velocity is not None else None
        for index, item in enumerate(detections):
            if item.get("xyz_m") is not None and index not in assigned_items:
                track = Track(self.next_id, item["label"], np.array(item["xyz_m"]), timestamp_ms)
                self.tracks[track.id] = track
                item["track_id"], item["velocity_m_s"] = track.id, None
                self.next_id += 1
        self.tracks = {i: t for i, t in self.tracks.items() if t.missed <= self.max_missed}
        return detections
