"""SDK-independent algorithms. Pinhole math explicitly rejects distortion."""
import numpy as np

from .models import Frame, Intrinsics


def require_pinhole(k: Intrinsics) -> None:
    if k.model not in ("none", "distortion.none"):
        raise ValueError("Distorted images require SDK deprojection or rectification")


def deproject(pixel, z: float, k: Intrinsics) -> np.ndarray:
    require_pinhole(k)
    x, y = pixel
    if not (0 <= x < k.width and 0 <= y < k.height):
        raise ValueError("Pixel outside image")
    if not np.isfinite(z) or z <= 0:
        raise ValueError("Invalid depth; never treat missing depth as free space")
    return np.array([(x-k.ppx)*z/k.fx, (y-k.ppy)*z/k.fy, z], dtype=float)


def robust_depth(depth: np.ndarray, pixel, radius: int = 2) -> tuple[float, float, int]:
    """Median, robust spread (MAD) and count; spread is not accuracy."""
    x, y = map(int, pixel)
    h, w = depth.shape
    if radius < 0 or not (0 <= x < w and 0 <= y < h):
        raise ValueError("Invalid pixel or neighborhood radius")
    patch = depth[max(0, y-radius):y+radius+1, max(0, x-radius):x+radius+1]
    valid = patch[np.isfinite(patch) & (patch > 0)]
    if not valid.size:
        raise ValueError("No valid depth in neighborhood")
    median = float(np.median(valid))
    return median, float(np.median(np.abs(valid-median))), int(valid.size)


def pointcloud(depth: np.ndarray, k: Intrinsics, stride: int = 2,
               max_depth: float = 5.) -> tuple[np.ndarray, np.ndarray]:
    """Return XYZ and corresponding (row, col) indices for color sampling."""
    require_pinhole(k)
    if stride < 1 or not np.isfinite(max_depth) or max_depth <= 0:
        raise ValueError("Invalid pointcloud sampling")
    if depth.shape != (k.height, k.width):
        raise ValueError("Depth dimensions differ from intrinsics")
    rows, cols = np.mgrid[0:k.height:stride, 0:k.width:stride]
    z = depth[::stride, ::stride]
    valid = np.isfinite(z) & (z > 0) & (z <= max_depth)
    z, rows, cols = z[valid], rows[valid], cols[valid]
    xyz = np.column_stack(((cols-k.ppx)*z/k.fx, (rows-k.ppy)*z/k.fy, z))
    return xyz, np.column_stack((rows, cols))


def fit_plane(points: np.ndarray, threshold: float = .015, iterations: int = 150,
              seed: int = 0) -> tuple[np.ndarray, np.ndarray]:
    """Deterministic RANSAC + SVD refinement; plane n.x+d=0, |n|=1."""
    points = np.asarray(points, dtype=float)
    if points.ndim != 2 or points.shape[1] != 3 or len(points) < 3:
        raise ValueError("At least three XYZ points required")
    if not np.isfinite(points).all() or threshold <= 0 or iterations < 1:
        raise ValueError("Invalid plane input")
    rng = np.random.default_rng(seed)
    best = np.zeros(len(points), dtype=bool)
    for _ in range(iterations):
        a, b, c = points[rng.choice(len(points), 3, replace=False)]
        n = np.cross(b-a, c-a)
        length = np.linalg.norm(n)
        if length < 1e-10:
            continue
        n /= length
        mask = np.abs(points @ n - a @ n) <= threshold
        if mask.sum() > best.sum():
            best = mask
    if best.sum() < 3:
        raise ValueError("Degenerate point set: no plane")
    centered = points[best] - points[best].mean(axis=0)
    _, singular, vt = np.linalg.svd(centered, full_matrices=False)
    if singular[1] < 1e-10:
        raise ValueError("Collinear plane inliers")
    normal = vt[-1]
    if normal[2] < 0:
        normal = -normal
    plane = np.r_[normal, -points[best].mean(axis=0) @ normal]
    return plane, np.abs(points @ normal + plane[3]) <= threshold


def bounding_box(points: np.ndarray) -> dict:
    """Axis-aligned visible-point extent, NOT the complete physical object size."""
    points = np.asarray(points)
    if points.ndim != 2 or points.shape[1] != 3 or not len(points):
        raise ValueError("Non-empty Nx3 point set required")
    if not np.isfinite(points).all():
        raise ValueError("Non-finite point")
    low, high = points.min(axis=0), points.max(axis=0)
    return {"min_m": low.tolist(), "max_m": high.tolist(),
            "visible_extent_m": (high-low).tolist()}


def frame_point(frame: Frame, pixel, radius: int = 2) -> tuple[np.ndarray, float, int]:
    z, mad, count = robust_depth(frame.depth_m, pixel, radius)
    x, y = map(int, pixel)
    point = (frame.rays[y, x] * z if frame.rays is not None
             else deproject((x, y), z, frame.intrinsics))
    return point, mad, count


def frame_cloud(frame: Frame, stride: int = 2, max_depth: float = 5.):
    if frame.rays is None:
        return pointcloud(frame.depth_m, frame.intrinsics, stride, max_depth)
    if stride < 1 or not np.isfinite(max_depth) or max_depth <= 0:
        raise ValueError("Invalid pointcloud sampling")
    rows, cols = np.mgrid[0:frame.intrinsics.height:stride, 0:frame.intrinsics.width:stride]
    z = frame.depth_m[::stride, ::stride]
    valid = np.isfinite(z) & (z > 0) & (z <= max_depth)
    pixels = np.column_stack((rows[valid], cols[valid]))
    return frame.rays[::stride, ::stride][valid] * z[valid, None], pixels
