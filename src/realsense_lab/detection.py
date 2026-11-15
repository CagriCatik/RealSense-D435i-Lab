"""Optional YOLO adapter. Weights must already exist locally."""
from pathlib import Path

from .geometry import frame_point


class Detector:
    def __init__(self, weights, confidence=.4):
        if not Path(weights).is_file():
            raise ValueError("Provide an existing local YOLO weights file; no implicit model download")
        if not 0 < confidence <= 1:
            raise ValueError("Confidence must be in (0, 1]")
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise RuntimeError("Install the [yolo] extra for object detection") from exc
        self.model, self.confidence = YOLO(str(weights)), confidence

    def predict(self, frame):
        # Ultralytics ndarray input uses BGR; our core Frame is always RGB.
        result = self.model.predict(source=frame.color[..., ::-1].copy(),
                                    conf=self.confidence, verbose=False)[0]
        detections = []
        for box in result.boxes:
            xyxy = box.xyxy[0].cpu().numpy().tolist()
            cx = min(frame.intrinsics.width-1, max(0, int((xyxy[0]+xyxy[2])/2)))
            cy = min(frame.intrinsics.height-1, max(0, int((xyxy[1]+xyxy[3])/2)))
            entry = {"label": result.names[int(box.cls.item())],
                     "confidence": float(box.conf.item()), "xyxy": xyxy,
                     "xyz_m": None, "depth_mad_m": None}
            try:
                xyz, mad, _ = frame_point(frame, (cx, cy))
                entry.update(xyz_m=xyz.tolist(), depth_mad_m=mad)
            except ValueError:
                pass
            detections.append(entry)
        return detections
