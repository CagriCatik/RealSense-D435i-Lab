"""Identical Frame interface for synthetic scenes and portable replay."""
from pathlib import Path

import numpy as np

from .models import Frame, Intrinsics
from .storage import load_frame


class SyntheticSource:
    def __init__(self, count=300, width=640, height=480, fps=30):
        if count < 1 or width < 8 or height < 8 or fps <= 0:
            raise ValueError("Invalid synthetic source dimensions/count/fps")
        self.count, self.width, self.height, self.fps = count, width, height, fps

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def __iter__(self):
        w, h = self.width, self.height
        k = Intrinsics(w, h, .9*w, .9*w, (w-1)/2, (h-1)/2)
        yy, xx = np.mgrid[:h, :w]
        for number in range(self.count):
            # Static foreground box on a 2-m background with repeatable noise.
            rng = np.random.default_rng(number)
            depth = np.full((h, w), 2., np.float32)
            depth[h//3:2*h//3, w//3:2*w//3] = 1.2
            depth += rng.normal(0, .002, depth.shape).astype(np.float32)
            depth[::31, ::29] = 0  # invalid stereo pixels
            color = np.zeros((h, w, 3), np.uint8)
            color[..., 0] = xx*255//w
            color[..., 1] = yy*255//h
            color[..., 2] = 100
            color[h//3:2*h//3, w//3:2*w//3] = (240, 180, 30)
            yield Frame(color, depth, k, number*1000/self.fps, number)


class ReplaySource:
    def __init__(self, path):
        path = Path(path)
        self.paths = sorted(path.glob("*.npz")) if path.is_dir() else [path]
        if not self.paths or any(not p.is_file() for p in self.paths):
            raise ValueError("No portable .npz frames found")

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def __iter__(self):
        for path in self.paths:
            yield load_frame(path)


class TabletopSource(SyntheticSource):
    """Known sloped support plane with two disjoint raised top surfaces.

    This ray-cast fixture is deliberately not a photorealistic or complete box model.
    The two surfaces are 0.12 and 0.18 meters above a plane facing the camera.
    """
    def __iter__(self):
        w, h = self.width, self.height
        k = Intrinsics(w, h, .9*w, .9*w, (w-1)/2, (h-1)/2)
        yy, xx = np.mgrid[:h, :w]
        rays = np.stack(((xx-k.ppx)/k.fx, (yy-k.ppy)/k.fy, np.ones((h, w))), axis=-1)
        normal = np.array([0., -.6, -.8])
        offset = 1.2
        denominator = rays @ normal
        base_depth = -offset/denominator
        depth = base_depth.copy()
        color = np.empty((h, w, 3), np.uint8)
        checker = (xx//24+yy//24) % 2
        color[:] = (85, 120, 100)
        color[checker == 0] = (95, 135, 110)
        tangent = np.array([0., -.8, .6])
        for center_u, center_v, extent_u, extent_v, height, rgb in (
                (-.22, .9, .22, .25, .12, (246, 189, 55)),
                (.23, .9, .18, .22, .18, (80, 162, 245))):
            raised_depth = (height-offset)/denominator
            xyz = rays*raised_depth[..., None]
            u, v = xyz[..., 0], xyz @ tangent
            mask = (np.abs(u-center_u) <= extent_u/2) & (np.abs(v-center_v) <= extent_v/2)
            depth[mask] = raised_depth[mask]
            color[mask] = rgb
        for number in range(self.count):
            rng = np.random.default_rng(number)
            measured = (depth+rng.normal(0., .0008, (h, w))).astype(np.float32)
            measured[::31, ::29] = 0
            yield Frame(color.copy(), measured, k, number*1000/self.fps, number)
