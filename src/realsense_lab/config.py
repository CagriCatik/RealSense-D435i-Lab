from dataclasses import asdict, dataclass, fields
import json
import math
from pathlib import Path


@dataclass(frozen=True)
class Config:
    depth_width: int = 848
    depth_height: int = 480
    color_width: int = 640
    color_height: int = 480
    fps: int = 30
    min_depth_m: float = .3
    max_depth_m: float = 3.
    spatial: bool = True
    temporal: bool = False  # opt-in: temporal persistence can trail moving objects
    hole_filling: bool = False
    serial: str = ""

    def __post_init__(self):
        for name in ("depth_width", "depth_height", "color_width", "color_height", "fps"):
            value = getattr(self, name)
            if type(value) is not int or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        for name in ("spatial", "temporal", "hole_filling"):
            if type(getattr(self, name)) is not bool:
                raise ValueError(f"{name} must be a boolean")
        limits = (self.min_depth_m, self.max_depth_m)
        if not all(type(v) in (int, float) and math.isfinite(v) for v in limits):
            raise ValueError("Depth limits must be finite numbers")
        if not 0 < self.min_depth_m < self.max_depth_m:
            raise ValueError("Expected 0 < min_depth_m < max_depth_m")
        if not isinstance(self.serial, str):
            raise ValueError("serial must be a string")

    @classmethod
    def load(cls, path: str | None):
        if not path:
            return cls()
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Config must be a JSON object")
        unknown = set(data) - {f.name for f in fields(cls)}
        if unknown:
            raise ValueError(f"Unknown configuration keys: {sorted(unknown)}")
        return cls(**data)

    def to_dict(self):
        return asdict(self)
