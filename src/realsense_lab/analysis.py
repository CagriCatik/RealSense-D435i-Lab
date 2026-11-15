"""Small application operations shared by CLI, GUI and replay."""
import numpy as np

from .geometry import bounding_box, fit_plane, frame_cloud


def summarize(frame, max_depth=3., stride=4):
    xyz, _ = frame_cloud(frame, stride, max_depth)
    valid = np.isfinite(frame.depth_m) & (frame.depth_m > 0) & (frame.depth_m <= max_depth)
    values = frame.depth_m[valid]
    result = {"frame_number": frame.number, "timestamp_ms": frame.timestamp_ms,
              "timestamp_domain": frame.timestamp_domain,
              "valid_fraction": float(valid.mean()), "sampled_points": len(xyz),
              "depth_percentiles_m": np.percentile(values, [5, 50, 95]).tolist() if len(values) else [],
              "coordinate_system": "optical: x right, y down, z forward; meters"}
    if len(xyz):
        result["visible_bounds"] = bounding_box(xyz)
    if len(xyz) >= 3:
        try:
            plane, inliers = fit_plane(xyz)
            result["dominant_plane"] = {"coefficients": plane.tolist(),
                                         "inlier_fraction": float(inliers.mean()),
                                         "threshold_m": .015}
        except ValueError as exc:
            result["plane_error"] = str(exc)
    return result


def frame_health(numbers, timestamps, domains, elapsed):
    """Throughput is host processing rate; gaps are observed sequence gaps only."""
    gaps, resets = 0, 0
    for before, after in zip(numbers, numbers[1:]):
        if after <= before:
            resets += 1
        else:
            gaps += max(0, after-before-1)
    dt = np.diff(timestamps)
    same_domain = len(set(domains)) <= 1
    positive = dt[dt > 0] if same_domain else np.array([])
    return {"frames": len(numbers), "host_elapsed_s": elapsed,
            "host_throughput_fps": len(numbers)/elapsed if elapsed > 0 else 0.,
            "observed_sequence_gaps": int(gaps), "sequence_resets_or_duplicates": resets,
            "timestamp_domains": sorted(set(domains)),
            "timestamp_nonpositive_steps": int(np.sum(dt <= 0)),
            "median_source_interval_ms": float(np.median(positive)) if positive.size else None,
            "note": "Sequence gaps are not an end-to-end loss measurement. Host rate includes processing/I/O."}
