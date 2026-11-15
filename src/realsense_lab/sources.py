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
