"""Offline motion diagnostics. No drift-free position claim or on-device writes."""
import csv

import numpy as np


def summarize_imu(path):
    grouped = {}
    with open(path, newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            values = [float(row[k]) for k in ("timestamp_ms", "x", "y", "z")]
            if not np.isfinite(values).all():
                raise ValueError("Non-finite IMU sample")
            grouped.setdefault((row["stream"], row["domain"]), []).append(values)
    if not grouped:
        raise ValueError("Empty IMU capture")
    report = {"groups": [], "assumption": "Bias interpretation requires camera stationary for entire capture"}
    for (name, domain), rows in sorted(grouped.items()):
        data = np.array(rows)
        dt = np.diff(data[:, 0])
        entry = {"stream": name, "domain": domain, "count": len(data),
                 "mean_xyz": data[:, 1:].mean(axis=0).tolist(),
                 "std_xyz": data[:, 1:].std(axis=0).tolist(),
                 "nonpositive_timestamp_steps": int(np.sum(dt <= 0)),
                 "median_rate_hz": float(1000/np.median(dt[dt > 0])) if np.any(dt > 0) else None}
        if "accel" in name:
            entry["mean_acceleration_norm_m_s2"] = float(np.linalg.norm(data[:, 1:].mean(axis=0)))
            entry["gravity_reference_m_s2"] = 9.80665
        report["groups"].append(entry)
    return report
