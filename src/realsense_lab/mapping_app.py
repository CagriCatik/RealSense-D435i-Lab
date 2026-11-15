"""Session output orchestration. Partial sessions retain an append-only journal."""
from dataclasses import asdict
import json
from pathlib import Path

from .mapping import LocalMapper
from .storage import save_frame, write_json, write_ply


def map_session(source, output, config, count, preview=None):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    mapper, entries, accepted = LocalMapper(config), [], []
    with (output/"tracking.jsonl").open("x", encoding="utf-8") as journal:
        for index, frame in enumerate(source):
            filename = f"frame_{index:06d}.npz"
            save_frame(output/filename, frame)
            entry = dict(mapper.update(frame), file=filename)
            journal.write(json.dumps(entry, allow_nan=False)+"\n")
            journal.flush()
            entries.append(entry)
            if entry["camera_to_world"] is not None:
                accepted.append({"file": filename, "camera_to_world": entry["camera_to_world"]})
            if preview is not None and not preview(frame, mapper, entry):
                break
            if index+1 >= count:
                break
    if not entries:
        raise ValueError("Mapping source produced no frames")
    xyz, colors = mapper.map.cloud()
    write_ply(output/"map.ply", xyz, colors)
    write_json(output/"manifest.json", {"schema": 1, "frames": accepted,
               "coordinate_system": "world = first camera optical frame; meters"})
    summary = {"mapping_schema": 1, "backend": "numpy_projective_point_to_plane",
               "status": "tracking_lost" if mapper.lost else "completed",
               "frames": len(entries), "accepted_frames": len(accepted),
               "map_voxels": len(xyz), "settings": asdict(config), "trajectory": entries,
               "limits": "Local depth odometry. Drift, no loop closure, no automatic recovery, no IMU fusion."}
    write_json(output/"trajectory.json", summary)
    return summary
