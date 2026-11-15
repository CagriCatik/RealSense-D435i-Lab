"""Pose chaining and bounded voxel fusion. Pure NumPy, no transport or UI."""
import numpy as np

from .geometry import frame_cloud, require_pinhole
from .odometry import MappingConfig, ProjectiveOdometry, transform_points, validate_pose


class VoxelMap:
    def __init__(self, voxel_m=.02, max_voxels=200000):
        if not np.isfinite(voxel_m) or voxel_m <= 0 or type(max_voxels) is not int or max_voxels < 1:
            raise ValueError("Invalid voxel map parameters")
        self.voxel_m, self.max_voxels = voxel_m, max_voxels
        self.voxels = {}

    def integrate(self, points, colors, pose):
        points, colors = np.asarray(points), np.asarray(colors)
        if points.ndim != 2 or points.shape[1] != 3 or colors.shape != points.shape:
            raise ValueError("Matching Nx3 points and RGB required")
        if not np.isfinite(points).all() or colors.dtype != np.uint8:
            raise ValueError("Finite points and uint8 RGB required")
        world = transform_points(points, pose)
        keys, inverse = np.unique(np.floor(world/self.voxel_m).astype(np.int64), axis=0, return_inverse=True)
        key_tuples = [tuple(row) for row in keys]
        if len(self.voxels)+sum(key not in self.voxels for key in key_tuples) > self.max_voxels:
            raise RuntimeError("voxel_capacity_exceeded")
        count = np.bincount(inverse, minlength=len(keys))
        values = np.column_stack((world, colors))
        sums = np.column_stack([np.bincount(inverse, weights=values[:, i], minlength=len(keys)) for i in range(6)])
        for index, key in enumerate(key_tuples):
            total, weight = self.voxels.get(key, (np.zeros(6), 0))
            self.voxels[key] = (total+sums[index], weight+int(count[index]))

    def cloud(self):
        if not self.voxels:
            return np.empty((0, 3)), np.empty((0, 3), np.uint8)
        mean = np.array([total/weight for _, (total, weight) in sorted(self.voxels.items())])
        return mean[:, :3], np.clip(np.rint(mean[:, 3:]), 0, 255).astype(np.uint8)


class LocalMapper:
    """Map origin is the first camera. Failure latches until a new session."""
    def __init__(self, config=None, estimator=None):
        self.config = config or MappingConfig()
        self.estimator = estimator or ProjectiveOdometry(self.config)
        self.map = VoxelMap(self.config.voxel_m, self.config.max_voxels)
        self.previous, self.pose, self.lost = None, np.eye(4), False

    def update(self, frame):
        entry = {"frame_number": frame.number, "timestamp_ms": frame.timestamp_ms,
                 "timestamp_domain": frame.timestamp_domain, "camera_to_world": None,
                 "status": "lost", "diagnostic": {}}
        if self.lost:
            return dict(entry, diagnostic={"reason": "tracking_lost_latched"})
        require_pinhole(frame.intrinsics)
        points, pixels = frame_cloud(frame, self.config.stride, self.config.max_depth_m)
        pose = self.pose.copy()
        if len(points) < self.config.min_correspondences:
            diagnostic = {"reason": "insufficient_depth"}
        elif self.previous is not None:
            if frame.timestamp_domain != self.previous.timestamp_domain or frame.timestamp_ms <= self.previous.timestamp_ms:
                diagnostic = {"reason": "timestamp_discontinuity"}
            else:
                relative, diagnostic = self.estimator.estimate(self.previous, frame)
                if relative is not None:
                    # Relative maps previous-camera -> current-camera.
                    # Therefore current-camera -> world = previous-world @ inverse(relative).
                    try:
                        pose = self.pose@np.linalg.inv(validate_pose(relative))
                    except (ValueError, np.linalg.LinAlgError):
                        diagnostic = {"reason": "invalid_estimate"}
                elif diagnostic.get("reason") == "accepted":
                    diagnostic = {"reason": "invalid_estimate"}
        else:
            diagnostic = {"reason": "initialized"}
        accepted = diagnostic["reason"] in ("initialized", "accepted")
        if accepted:
            try:
                self.map.integrate(points, frame.color[pixels[:, 0], pixels[:, 1]], pose)
            except RuntimeError as exc:
                diagnostic, accepted = {"reason": str(exc)}, False
        if not accepted:
            self.lost = True
            return dict(entry, diagnostic=diagnostic)
        self.previous, self.pose = frame, pose
        return dict(entry, status="initialized" if diagnostic["reason"] == "initialized" else "tracking",
                    camera_to_world=pose.tolist(), diagnostic=diagnostic)
