"""OpenCV annotation adapter; segmentation colors are computed in NumPy."""
from .scene_render import PALETTE, segmentation_rgb


def annotate_scene(cv, rgb_bgr, frame, result, stride):
    report = result.report
    for obj in report["objects"]:
        color = tuple(int(v) for v in PALETTE[(obj["segment_id"]-1) % len(PALETTE)][::-1])
        x0, y0, x1, y1 = obj["bbox_xyxy"]
        cv.rectangle(rgb_bgr, (x0, y0), (x1, y1), color, 2)
        u, v, _ = obj["visible_extent_plane_m"]
        height = obj["height_above_reference_m"]
        text = f"#{obj['track_id']} visible {u*100:.1f} x {v*100:.1f} cm | H {height*100:.1f} cm"
        cv.putText(rgb_bgr, text, (max(0, x0), max(45, y0-8)),
                   cv.FONT_HERSHEY_SIMPLEX, .43, color, 1)
    title = f"{report['status']} | {len(report['objects'])} objects | fixed camera required"
    cv.putText(rgb_bgr, title, (10, 43), cv.FONT_HERSHEY_SIMPLEX, .45, (240, 240, 240), 1)
    h, w = frame.depth_m.shape
    return segmentation_rgb(result, h, w, stride)[..., ::-1].copy()
