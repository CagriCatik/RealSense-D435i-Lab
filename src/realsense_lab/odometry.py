"""Local geometric RGB-D odometry. No IMU, loop closure or relocalization."""
from dataclasses import dataclass
import json
from pathlib import Path

import numpy as np

from .geometry import frame_cloud, require_pinhole


@dataclass(frozen=True)
class MappingConfig:
    stride: int = 4
    max_depth_m: float = 3.
    correspondence_m: float = .08
    normal_edge_m: float = .05
    min_correspondences: int = 100
    min_overlap: float = .3
    max_rmse_m: float = .012
    max_translation_m: float = .12
    max_rotation_rad: float = .2
    max_condition: float = 1e6
    iterations: int = 30
    voxel_m: float = .02
    max_voxels: int = 200000

    def __post_init__(self):
        for name in ("stride", "min_correspondences", "iterations", "max_voxels"):
            if type(getattr(self, name)) is not int or getattr(self, name) < 1:
                raise ValueError(f"{name} must be a positive integer")
        for name in ("max_depth_m", "correspondence_m", "normal_edge_m", "max_rmse_m",
                     "max_translation_m", "max_rotation_rad", "max_condition", "voxel_m"):
            value = getattr(self, name)
            if type(value) not in (int, float) or not np.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be finite and positive")
        if type(self.min_overlap) not in (int, float) or not 0 < self.min_overlap <= 1:
            raise ValueError("min_overlap must be in (0,1]")
        if self.min_correspondences < 6 or self.max_condition <= 1:
            raise ValueError("At least six correspondences and max_condition >1 required")

    @classmethod
    def load(cls, path=None):
        if path is None:
            return cls()
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(data, dict) or set(data)-set(cls.__dataclass_fields__):
            raise ValueError("Mapping config must be an object with known keys")
        return cls(**data)


def rotation_vector(vector):
    vector = np.asarray(vector, dtype=float)
    angle = np.linalg.norm(vector)
    if angle < 1e-12:
        return np.eye(3)
    x, y, z = vector/angle
    skew = np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]])
    return np.eye(3)+np.sin(angle)*skew+(1-np.cos(angle))*(skew@skew)


def validate_pose(pose):
    pose = np.asarray(pose, dtype=float)
    if pose.shape != (4, 4) or not np.isfinite(pose).all():
        raise ValueError("Pose must be finite 4x4")
    r = pose[:3, :3]
    if (not np.allclose(pose[3], [0, 0, 0, 1])
            or not np.allclose(r.T@r, np.eye(3), atol=1e-5)
            or not np.isclose(np.linalg.det(r), 1., atol=1e-5)):
        raise ValueError("Pose must be a rigid transform")
    return pose


def transform_points(points, pose):
    pose = validate_pose(pose)
    return np.asarray(points) @ pose[:3, :3].T + pose[:3, 3]


def _target_geometry(frame, cfg):
    k, depth = frame.intrinsics, frame.depth_m
    yy, xx = np.mgrid[:k.height, :k.width]
    valid = np.isfinite(depth) & (depth > 0) & (depth <= cfg.max_depth_m)
    z = np.where(valid, depth, 0.)
    xyz = np.stack(((xx-k.ppx)*z/k.fx, (yy-k.ppy)*z/k.fy, z), axis=-1)
    dx = xyz[1:-1, 2:]-xyz[1:-1, :-2]
    dy = xyz[2:, 1:-1]-xyz[:-2, 1:-1]
    n = np.cross(dx, dy)
    length = np.linalg.norm(n, axis=-1)
    okay = (valid[1:-1, 1:-1] & valid[1:-1, 2:] & valid[1:-1, :-2]
            & valid[2:, 1:-1] & valid[:-2, 1:-1] & (length > 1e-10)
            & (np.abs(z[1:-1, 2:]-z[1:-1, :-2]) <= cfg.normal_edge_m)
            & (np.abs(z[2:, 1:-1]-z[:-2, 1:-1]) <= cfg.normal_edge_m))
    normals = np.zeros_like(xyz)
    normals[1:-1, 1:-1] = np.divide(n, length[..., None], out=np.zeros_like(n), where=okay[..., None])
    return xyz, normals


def _correspondences(points, transform, target, normals, k, cfg):
    moved = transform_points(points, transform)
    front = moved[:, 2] > .01
    projected = moved[front]
    x = np.rint(k.fx*projected[:, 0]/projected[:, 2]+k.ppx).astype(int)
    y = np.rint(k.fy*projected[:, 1]/projected[:, 2]+k.ppy).astype(int)
    inside = (x >= 1) & (x < k.width-1) & (y >= 1) & (y < k.height-1)
    p, x, y = projected[inside], x[inside], y[inside]
    q, n = target[y, x], normals[y, x]
    accepted = (np.linalg.norm(n, axis=1) > .5) & (np.linalg.norm(p-q, axis=1) <= cfg.correspondence_m)
    return p[accepted], q[accepted], n[accepted]


class ProjectiveOdometry:
    """Estimate source-camera -> target-camera with point-to-plane ICP."""
    def __init__(self, config=None):
        self.config = config or MappingConfig()

    def estimate(self, source, target):
        cfg = self.config
        require_pinhole(source.intrinsics)
        require_pinhole(target.intrinsics)
        if source.intrinsics != target.intrinsics:
            return None, {"reason": "camera_geometry_changed"}
        points, _ = frame_cloud(source, cfg.stride, cfg.max_depth_m)
        if len(points) < cfg.min_correspondences:
            return None, {"reason": "insufficient_source_depth"}
        target_xyz, normals = _target_geometry(target, cfg)
        transform = np.eye(4)
        diagnostic = {}
        converged = False
        for iteration in range(cfg.iterations):
            p, q, n = _correspondences(points, transform, target_xyz, normals, target.intrinsics, cfg)
            diagnostic = {"correspondences": len(p), "overlap": len(p)/len(points), "iterations": iteration+1}
            if len(p) < cfg.min_correspondences or len(p)/len(points) < cfg.min_overlap:
                return None, dict(diagnostic, reason="insufficient_overlap")
            residual = np.sum(n*(p-q), axis=1)
            jacobian = np.column_stack((np.cross(p, n), n))
            weight = np.minimum(1., .01/np.maximum(np.abs(residual), 1e-12))
            hessian = jacobian.T @ (weight[:, None]*jacobian)
            values = np.linalg.eigvalsh(hessian)
            if values[0] <= 0 or values[-1]/values[0] > cfg.max_condition:
                return None, dict(diagnostic, reason="degenerate_geometry")
            try:
                delta = np.linalg.solve(hessian, -jacobian.T @ (weight*residual))
            except np.linalg.LinAlgError:
                return None, dict(diagnostic, reason="numerical_failure")
            update = np.eye(4)
            update[:3, :3], update[:3, 3] = rotation_vector(delta[:3]), delta[3:]
            transform = update@transform
            diagnostic["condition"] = float(values[-1]/values[0])
            if np.linalg.norm(delta) < 1e-5:
                converged = True
                break
        p, q, n = _correspondences(points, transform, target_xyz, normals, target.intrinsics, cfg)
        if len(p) < cfg.min_correspondences or len(p)/len(points) < cfg.min_overlap:
            return None, dict(diagnostic, reason="insufficient_final_overlap")
        rmse = float(np.sqrt(np.mean(np.sum(n*(p-q), axis=1)**2)))
        angle = float(np.arccos(np.clip((np.trace(transform[:3, :3])-1)/2, -1, 1)))
        diagnostic.update(rmse_m=rmse, translation_m=float(np.linalg.norm(transform[:3, 3])), rotation_rad=angle)
        if not converged:
            return None, dict(diagnostic, reason="iteration_limit")
        if rmse > cfg.max_rmse_m:
            return None, dict(diagnostic, reason="residual_too_large")
        if diagnostic["translation_m"] > cfg.max_translation_m or angle > cfg.max_rotation_rad:
            return None, dict(diagnostic, reason="motion_gate_exceeded")
        return transform, dict(diagnostic, reason="accepted")
