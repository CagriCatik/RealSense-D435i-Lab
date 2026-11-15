"""OpenCV UI adapter: RGB, depth and top-down cloud. Freeze before measuring."""
from datetime import datetime, timezone
from pathlib import Path
import time

import numpy as np

from .geometry import frame_cloud, frame_point
from .storage import save_frame, write_json, write_ply
from .tracking import Tracker


def cv_module():
    try:
        import cv2
        return cv2
    except ImportError as exc:
        raise RuntimeError("Install the [viewer] extra and use a desktop session") from exc


def output_stem(directory):
    return Path(directory) / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")


def cloud_image(frame, maximum):
    xyz, pixels = frame_cloud(frame, 4, maximum)
    h, w = frame.depth_m.shape
    image = np.zeros((h, w, 3), np.uint8)
    if not len(xyz):
        return image
    # Bird's-eye: camera at bottom center; z forward/up, x right.
    col = ((xyz[:, 0]/maximum+.5)*w).astype(int)
    row = (h-1-xyz[:, 2]/maximum*(h-1)).astype(int)
    mask = (row >= 0) & (row < h) & (col >= 0) & (col < w)
    rgb = frame.color[pixels[:, 0], pixels[:, 1]]
    image[row[mask], col[mask]] = rgb[mask, ::-1]
    return image


def show(source, config, output="artifacts", detector=None, scene_inspector=None):
    cv = cv_module()
    title = ("D435i Scene Inspector | RGB - Depth - Segments" if scene_inspector
             else "D435i Lab | RGB - Depth - Bird's-eye")
    cv.namedWindow(title, cv.WINDOW_AUTOSIZE)
    state = {"frame": None, "frozen": False, "points": [], "message": "Space: freeze before measuring"}

    def click(event, x, y, flags, param):
        if event != cv.EVENT_LBUTTONDOWN or not state["frozen"]:
            return
        frame = state["frame"]
        if frame is None or x >= frame.intrinsics.width or y >= frame.intrinsics.height:
            return  # clicks are measured only in the left (RGB) panel
        try:
            xyz, mad, count = frame_point(frame, (x, y))
            if len(state["points"]) == 2:
                state["points"].clear()
            state["points"].append({"pixel": [x, y], "xyz_m": xyz.tolist(),
                                     "depth_mad_m": mad, "valid_neighbors": count})
            state["message"] = f"XYZ {xyz.round(3)} m | depth MAD {mad:.4f} m"
            if len(state["points"]) == 2:
                a, b = [np.array(p["xyz_m"]) for p in state["points"]]
                state["message"] = f"3D distance: {np.linalg.norm(a-b):.4f} m (same frozen frame)"
        except ValueError as exc:
            state["message"] = str(exc)

    cv.setMouseCallback(title, click)
    iterator = iter(source)
    detections = []
    tracker = Tracker()
    scene_result = None
    scene_dirty = True
    try:
        while True:
            tick = time.monotonic()
            if not state["frozen"]:
                try:
                    state["frame"] = next(iterator)
                    scene_dirty = True
                except StopIteration:
                    break
                if detector:
                    detections = tracker.update(detector.predict(state["frame"]),
                                                state["frame"].timestamp_ms)
            frame = state["frame"]
            if scene_inspector and scene_dirty:
                try:
                    scene_result = scene_inspector.inspect(frame)
                except ValueError as exc:
                    scene_result = None
                    state["message"] = str(exc)
                scene_dirty = False
            rgb = frame.color[..., ::-1].copy()
            right_panel = cloud_image(frame, config.max_depth_m)
            if scene_result is not None:
                from .scene_view import annotate_scene
                right_panel = annotate_scene(cv, rgb, frame, scene_result, scene_inspector.config.stride)
            for detection in detections:
                x1, y1, x2, y2 = map(int, detection["xyxy"])
                xyz = detection["xyz_m"]
                text = detection["label"] + (f" Z={xyz[2]:.2f}m" if xyz else " depth unknown")
                if "track_id" in detection:
                    text = f"#{detection['track_id']} " + text
                cv.rectangle(rgb, (x1, y1), (x2, y2), (40, 230, 40), 2)
                cv.putText(rgb, text, (x1, max(20, y1)), cv.FONT_HERSHEY_SIMPLEX, .5, (40, 230, 40), 1)
            for point in state["points"]:
                cv.circle(rgb, tuple(point["pixel"]), 5, (20, 20, 255), -1)
            valid = np.isfinite(frame.depth_m) & (frame.depth_m > 0)
            normalized = np.clip(np.nan_to_num(frame.depth_m)/config.max_depth_m*255, 0, 255).astype(np.uint8)
            depth = cv.applyColorMap(255-normalized, cv.COLORMAP_TURBO)
            depth[~valid] = 0
            canvas = np.hstack((rgb, depth, right_panel))
            cv.putText(canvas, "FROZEN" if state["frozen"] else "LIVE / REPLAY", (10, 23),
                       cv.FONT_HERSHEY_SIMPLEX, .6, (255, 255, 255), 2)
            cv.putText(canvas, state["message"], (10, canvas.shape[0]-35),
                       cv.FONT_HERSHEY_SIMPLEX, .5, (255, 255, 255), 1)
            help_text = "Space freeze | click 2 RGB points | S snapshot | P PLY | M measurement | Q quit"
            if scene_inspector:
                help_text += " | C recalibrate | S scene+snapshot"
            cv.putText(canvas, help_text,
                       (10, canvas.shape[0]-12), cv.FONT_HERSHEY_SIMPLEX, .45, (255, 255, 255), 1)
            cv.imshow(title, canvas)
            key = cv.waitKey(10) & 0xff
            if key in (ord("q"), 27) or cv.getWindowProperty(title, cv.WND_PROP_VISIBLE) < 1:
                break
            if key == ord(" "):
                state["frozen"] = not state["frozen"]
                state["points"].clear()
            stem = output_stem(output)
            if key == ord("c") and scene_inspector:
                scene_inspector.reset()
                scene_result, scene_dirty = None, True
                state["message"] = "Recalibrating reference; camera must remain fixed"
            if key == ord("s"):
                if scene_inspector and scene_result is not None:
                    from .scene_io import save_scene
                    save_scene(stem, frame, scene_result, export_cloud=True)
                    state["message"] = f"Saved scene JSON + RGB-D + object PLY: {stem.name}"
                elif scene_inspector:
                    state["message"] = "No valid scene result to save; choose a clear reference ROI"
                else:
                    save_frame(stem.with_suffix(".npz"), frame)
                    state["message"] = f"Saved {stem.name}.npz"
            if key == ord("p"):
                xyz, pixels = frame_cloud(frame, 2, config.max_depth_m)
                write_ply(stem.with_suffix(".ply"), xyz, frame.color[pixels[:, 0], pixels[:, 1]])
                state["message"] = f"Exported {len(xyz)} points"
            if key == ord("m") and len(state["points"]) == 2:
                a, b = [np.array(p["xyz_m"]) for p in state["points"]]
                write_json(stem.with_suffix(".json"), {"frame_number": frame.number,
                    "timestamp_ms": frame.timestamp_ms, "points": state["points"],
                    "distance_m": float(np.linalg.norm(a-b)),
                    "note": "Median neighborhood depth. MAD is spread, not calibrated uncertainty."})
                state["message"] = "Measurement saved"
            if not state["frozen"]:
                remaining = 1/config.fps-(time.monotonic()-tick)
                if remaining > 0:
                    time.sleep(remaining)
    finally:
        cv.destroyAllWindows()
