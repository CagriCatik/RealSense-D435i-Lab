"""Core values: meters, milliseconds and optical camera coordinates."""
from dataclasses import dataclass
import math

import numpy as np


@dataclass(frozen=True)
class Intrinsics:
    width: int
    height: int
    fx: float
    fy: float
    ppx: float
    ppy: float
    model: str = "none"
    coeffs: tuple[float, ...] = (0., 0., 0., 0., 0.)

    def __post_init__(self):
        values = (self.fx, self.fy, self.ppx, self.ppy, *self.coeffs)
        if self.width <= 0 or self.height <= 0 or not all(map(math.isfinite, values)):
            raise ValueError("Invalid intrinsics")
        if self.fx <= 0 or self.fy <= 0 or len(self.coeffs) != 5:
            raise ValueError("Focal lengths must be positive; five distortion coefficients required")


@dataclass
class Frame:
    color: np.ndarray  # RGB uint8, not OpenCV BGR
    depth_m: np.ndarray  # axial Z in meters; zero/non-finite means invalid
    intrinsics: Intrinsics  # same geometry as depth and color
    timestamp_ms: float
    number: int
    timestamp_domain: str = "synthetic"
    rays: np.ndarray | None = None  # SDK-deprojected unit-Z rays for distorted images

    def __post_init__(self):
        expected = (self.intrinsics.height, self.intrinsics.width)
        if self.color.shape != (*expected, 3) or self.depth_m.shape != expected:
            raise ValueError("Color, aligned depth and intrinsics must have equal dimensions")
        if self.color.dtype != np.uint8 or not np.issubdtype(self.depth_m.dtype, np.floating):
            raise ValueError("Expected RGB uint8 and floating-point meter depth")
        if not math.isfinite(self.timestamp_ms) or self.number < 0:
            raise ValueError("Invalid frame identity")
        if self.rays is not None:
            if self.rays.shape != (*expected, 3) or not np.isfinite(self.rays).all():
                raise ValueError("Invalid deprojection rays")
            if not np.allclose(self.rays[..., 2], 1.):
                raise ValueError("Deprojection rays must have unit Z")
