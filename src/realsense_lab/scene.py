"""Stationary reference-plane inspection, independent of SDK, GUI and ML."""
from dataclasses import asdict, dataclass
import json
from pathlib import Path

import numpy as np

from .geometry import fit_plane, frame_cloud
from .tracking import Tracker


@dataclass(frozen=True)
class SceneConfig:
    stride: int = 4
    plane_threshold_m: float = .008
    min_height_m: float = .025
    max_height_m: float = .5
    cluster_gap_m: float = .06
    min_object_points: int = 25
    min_plane_points: int = 100
    min_plane_fraction: float = .5
    max_fit_points: int = 4000
    max_depth_m: float = 3.
    reference_roi: tuple = (0., 0., 1., 1.)  # normalized x0,y0,x1,y1

    def __post_init__(self):
        for name in ("stride", "min_object_points", "min_plane_points", "max_fit_points"):
            value = getattr(self, name)
            if type(value) is not int or value < 1:
                raise ValueError(f"{name} must be a positive integer")
        for name in ("plane_threshold_m", "min_height_m", "max_height_m", "cluster_gap_m", "max_depth_m"):
            value = getattr(self, name)
            if type(value) not in (int, float) or not np.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be positive and finite")
        if not self.plane_threshold_m < self.min_height_m < self.max_height_m:
            raise ValueError("Require plane_threshold_m < min_height_m < max_height_m")
        if type(self.min_plane_fraction) not in (int, float) or not .1 <= self.min_plane_fraction <= 1:
            raise ValueError("min_plane_fraction must be in [0.1, 1]")
        if self.min_plane_points < 3 or self.max_fit_points < self.min_plane_points:
            raise ValueError("Plane fitting needs >=3 points and enough max_fit_points")
        roi = self.reference_roi
        if (not isinstance(roi, (list, tuple)) or len(roi) != 4
                or not all(type(v) in (int, float) and np.isfinite(v) for v in roi)
                or not (0 <= roi[0] < roi[2] <= 1 and 0 <= roi[1] < roi[3] <= 1)):
            raise ValueError("reference_roi must be normalized [x0,y0,x1,y1]")

    @classmethod
    def load(cls, path=None):
        if path is None:
            return cls()
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(data, dict) or set(data)-set(cls.__dataclass_fields__):
            raise ValueError("Scene config must be an object with known keys")
        return cls(**data)


@dataclass
class SceneResult:
    report: dict
    labels: np.ndarray  # sampled grid: -1 unknown, -2 other, -3 unclustered, 0 surface
    points: np.ndarray
    pixels: np.ndarray


def _roi_mask(pixels, k, roi):
    y, x = pixels[:, 0], pixels[:, 1]
    return ((x >= roi[0]*k.width) & (x < roi[2]*k.width)
            & (y >= roi[1]*k.height) & (y < roi[3]*k.height))


def _components(points, cells, candidates, shape, gap, minimum):
    """8-connected sampled image regions, additionally gated by 3D separation."""
    lookup = np.full(shape, -1, dtype=np.int32)
    active = np.flatnonzero(candidates)
    lookup[cells[active, 0], cells[active, 1]] = active
    neighbors = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))
    groups = []
    visited = np.zeros(len(points), dtype=bool)
    for start in active:
        if visited[start]:
            continue
        visited[start] = True
        stack, group = [start], []
        while stack:
            index = stack.pop()
            group.append(index)
            y, x = cells[index]
            for dy, dx in neighbors:
                yy, xx = y+dy, x+dx
                if not (0 <= yy < shape[0] and 0 <= xx < shape[1]):
                    continue
                other = lookup[yy, xx]
                if other < 0 or visited[other]:
                    continue
                if np.sum((points[index]-points[other])**2) <= gap*gap:
                    visited[other] = True
                    stack.append(other)
        if len(group) >= minimum:
            groups.append(np.array(group))
    return groups


def _plane_basis(normal):
    axis = np.array([1., 0., 0.])
    if abs(normal @ axis) > .9:
        axis = np.array([0., 1., 0.])
    u = axis-normal*(normal @ axis)
    u /= np.linalg.norm(u)
    return np.column_stack((u, np.cross(normal, u), normal))


def _intrinsic_dict(k):
    result = asdict(k)
    result["coeffs"] = list(k.coeffs)
    return result


class SceneInspector:
    """A calibrated plane stays fixed until explicit reset/recalibration."""
    def __init__(self, config=None):
        self.config = config or SceneConfig()
        self.plane = self.intrinsics = self.calibration = None
        self.tracker = Tracker(gate_m=.15, max_missed=5)

    def reset(self):
        self.plane = self.intrinsics = self.calibration = None
        self.tracker = Tracker(gate_m=.15, max_missed=5)

    def calibrate(self, frame):
        cfg = self.config
        points, pixels = frame_cloud(frame, cfg.stride, cfg.max_depth_m)
        selected = points[_roi_mask(pixels, frame.intrinsics, cfg.reference_roi)]
        if len(selected) < cfg.min_plane_points:
            raise ValueError("Not enough reference ROI points; adjust ROI/depth or camera view")
        if len(selected) > cfg.max_fit_points:
            selected = selected[np.random.default_rng(0).choice(len(selected), cfg.max_fit_points, replace=False)]
        plane, inliers = fit_plane(selected, cfg.plane_threshold_m)
        if inliers.sum() < cfg.min_plane_points or inliers.mean() < cfg.min_plane_fraction:
            raise ValueError("Reference ROI has no dominant plane; choose a clear support surface")
        # Positive height points toward the camera, never infer gravity from a plane.
        if plane[3] < 0:
            plane = -plane
        if abs(plane[3]) <= cfg.plane_threshold_m:
            raise ValueError("Reference plane passes too close to camera origin")
        self.plane, self.intrinsics = plane, frame.intrinsics
        self.calibration = {"frame_number": frame.number, "timestamp_ms": frame.timestamp_ms,
                            "timestamp_domain": frame.timestamp_domain,
                            "roi": list(cfg.reference_roi), "fit_inlier_fraction": float(inliers.mean())}
        self.tracker = Tracker(gate_m=.15, max_missed=5)

    def inspect(self, frame):
        if self.plane is None:
            self.calibrate(frame)
        if frame.intrinsics != self.intrinsics:
            raise ValueError("Camera geometry changed; explicitly reset the scene reference")
        cfg = self.config
        points, pixels = frame_cloud(frame, cfg.stride, cfg.max_depth_m)
        cells = pixels//cfg.stride
        shape = ((frame.intrinsics.height+cfg.stride-1)//cfg.stride,
                 (frame.intrinsics.width+cfg.stride-1)//cfg.stride)
        labels = np.full(shape, -1, np.int32)
        heights = points @ self.plane[:3] + self.plane[3]
        support = np.abs(heights) <= cfg.plane_threshold_m
        roi = _roi_mask(pixels, frame.intrinsics, cfg.reference_roi)
        fraction = float(support[roi].mean()) if roi.any() else 0.
        okay = np.sum(support & roi) >= cfg.min_plane_points and fraction >= cfg.min_plane_fraction
        labels[cells[:, 0], cells[:, 1]] = -2
        labels[cells[support, 0], cells[support, 1]] = 0
        report = {"scene_schema": 1, "status": "ok" if okay else "reference_lost",
                  "frame_number": frame.number, "timestamp_ms": frame.timestamp_ms,
                  "timestamp_domain": frame.timestamp_domain,
                  "intrinsics": _intrinsic_dict(frame.intrinsics), "settings": asdict(cfg),
                  "calibration": self.calibration, "reference_plane": self.plane.tolist(),
                  "reference_inlier_fraction": fraction,
                  "valid_sample_fraction": float(len(points)/labels.size),
                  "reference_rmse_m": float(np.sqrt(np.mean(heights[support]**2))) if support.any() else None,
                  "objects": [], "coordinate_system": "camera optical, meters; stationary camera required",
                  "limits": "Camera-facing reference, not gravity. Visible extents, not complete physical dimensions."}
        if not okay:
            self.tracker.update([], frame.timestamp_ms)
            return SceneResult(report, labels, points, pixels)
        candidates = (heights >= cfg.min_height_m) & (heights <= cfg.max_height_m)
        labels[cells[candidates, 0], cells[candidates, 1]] = -3
        groups = _components(points, cells, candidates, shape, cfg.cluster_gap_m, cfg.min_object_points)
        basis = _plane_basis(self.plane[:3])
        for object_id, indices in enumerate(groups, 1):
            xyz, px = points[indices], pixels[indices]
            aligned = xyz @ basis
            labels[cells[indices, 0], cells[indices, 1]] = object_id
            report["objects"].append({
                "segment_id": object_id, "label": "geometry_object", "sampled_points": len(indices),
                "xyz_m": np.median(xyz, axis=0).tolist(),
                "bbox_xyxy": [int(px[:, 1].min()), int(px[:, 0].min()),
                              int(px[:, 1].max()), int(px[:, 0].max())],
                "visible_extent_camera_m": np.ptp(xyz, axis=0).tolist(),
                "visible_extent_plane_m": np.ptp(aligned, axis=0).tolist(),
                "height_above_reference_m": float(np.percentile(heights[indices], 95)),
                "height_median_m": float(np.median(heights[indices]))})
        self.tracker.update(report["objects"], frame.timestamp_ms)
        return SceneResult(report, labels, points, pixels)


def compare_scenes(current, baseline, gate_m=.15):
    """One-to-one camera-frame association; no cross-pose comparison is inferred."""
    for report in (current, baseline):
        if not isinstance(report, dict) or report.get("scene_schema") != 1 or report.get("status") != "ok":
            raise ValueError("Comparison requires two successful scene_schema=1 reports")
        if not isinstance(report.get("objects"), list):
            raise ValueError("Scene report objects must be a list")
        for obj in report["objects"]:
            if not isinstance(obj, dict):
                raise ValueError("Each scene object must be an object")
            for key in ("xyz_m", "visible_extent_plane_m"):
                values = np.asarray(obj.get(key), dtype=float)
                if values.shape != (3,) or not np.isfinite(values).all():
                    raise ValueError(f"Baseline object needs finite {key} XYZ values")
            height = obj.get("height_above_reference_m")
            if type(height) not in (float, int) or not np.isfinite(height):
                raise ValueError("Baseline object height must be finite")
            if type(obj.get("segment_id")) is not int:
                raise ValueError("Baseline object needs an integer segment_id")
    if current["intrinsics"] != baseline["intrinsics"]:
        raise ValueError("Baseline camera geometry differs")
    a, b = np.array(current["reference_plane"]), np.array(baseline["reference_plane"])
    if a.shape != (4,) or b.shape != (4,) or not np.isfinite([a, b]).all():
        raise ValueError("Invalid baseline reference plane")
    if not all(np.isclose(np.linalg.norm(p[:3]), 1., atol=1e-5) for p in (a, b)):
        raise ValueError("Reference plane normal must have unit length")
    if a[:3] @ b[:3] < .995 or abs(a[3]-b[3]) > .02:
        raise ValueError("Baseline reference plane differs; compare only the same fixed setup")
    if not np.isfinite(gate_m) or gate_m <= 0:
        raise ValueError("Positive baseline matching gate required")
    pairs = []
    for i, obj in enumerate(current["objects"]):
        for j, ref in enumerate(baseline["objects"]):
            distance = float(np.linalg.norm(np.array(obj["xyz_m"])-ref["xyz_m"]))
            if distance <= gate_m:
                pairs.append((distance, i, j))
    used_current, used_baseline, matches = set(), set(), []
    for distance, i, j in sorted(pairs):
        if i in used_current or j in used_baseline:
            continue
        obj, ref = current["objects"][i], baseline["objects"][j]
        matches.append({"current_segment_id": obj["segment_id"], "baseline_segment_id": ref["segment_id"],
                        "center_distance_m": distance,
                        "delta_xyz_m": (np.array(obj["xyz_m"])-ref["xyz_m"]).tolist(),
                        "delta_height_m": obj["height_above_reference_m"]-ref["height_above_reference_m"],
                        "delta_visible_extent_plane_m": (np.array(obj["visible_extent_plane_m"])-ref["visible_extent_plane_m"]).tolist()})
        used_current.add(i)
        used_baseline.add(j)
    return {"matches": matches, "unmatched_current": len(current["objects"])-len(used_current),
            "unmatched_baseline": len(baseline["objects"])-len(used_baseline),
            "note": "Same fixed camera required. Plane agreement does not prove an unchanged camera pose."}
