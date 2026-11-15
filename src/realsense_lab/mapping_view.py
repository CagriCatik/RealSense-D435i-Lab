"""Optional live top-down map/trajectory preview in the initial optical frame."""
import numpy as np

from .viewer import cv_module


class MapPreview:
    def __init__(self):
        self.cv = cv_module()
        self.title = "D435i Local Mapping | RGB - map X/Z | Q stop"
        self.path = []

    def __call__(self, frame, mapper, entry):
        cv = self.cv
        h, w = frame.depth_m.shape
        panel = np.full((h, w, 3), 15, np.uint8)
        xyz, rgb = mapper.map.cloud()
        scale = min(w, h)/6.

        def pixels(points):
            return np.column_stack((w/2+points[:, 0]*scale, h-35-points[:, 2]*scale)).astype(int)

        if len(xyz):
            xy = pixels(xyz)
            valid = (xy[:, 0] >= 0) & (xy[:, 0] < w) & (xy[:, 1] >= 0) & (xy[:, 1] < h)
            panel[xy[valid, 1], xy[valid, 0]] = rgb[valid, ::-1]
        if entry["camera_to_world"] is not None:
            self.path.append(np.asarray(entry["camera_to_world"])[:3, 3])
        if self.path:
            path = pixels(np.array(self.path))
            for a, b in zip(path, path[1:]):
                cv.line(panel, tuple(a), tuple(b), (20, 220, 240), 2)
            cv.circle(panel, tuple(path[-1]), 4, (20, 220, 240), -1)
        image = np.hstack((frame.color[..., ::-1].copy(), panel))
        text = f"{entry['status']} | {entry['diagnostic']['reason']} | {len(xyz)} voxels"
        color = (30, 30, 255) if entry["status"] == "lost" else (240, 240, 240)
        cv.putText(image, text, (10, 23), cv.FONT_HERSHEY_SIMPLEX, .55, color, 2)
        cv.imshow(self.title, image)
        return cv.waitKey(1) & 0xff not in (ord("q"), 27)

    def close(self):
        self.cv.destroyAllWindows()
