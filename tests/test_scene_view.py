import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import numpy as np

from realsense_lab.config import Config
from realsense_lab.scene import SceneConfig, SceneInspector
from realsense_lab.sources import TabletopSource
from realsense_lab.viewer import show


class SceneViewTests(unittest.TestCase):
    def test_freeze_recalibrate_and_paired_save_through_ui_boundary(self):
        cv = MagicMock()
        cv.WINDOW_AUTOSIZE, cv.FONT_HERSHEY_SIMPLEX, cv.COLORMAP_TURBO = 1, 0, 20
        cv.EVENT_LBUTTONDOWN, cv.WND_PROP_VISIBLE = 1, 0
        cv.getWindowProperty.return_value = 1
        cv.waitKey.side_effect = [ord(" "), ord("c"), ord("s"), ord("q")]
        cv.applyColorMap.side_effect = lambda image, palette: np.repeat(image[..., None], 3, axis=2)
        inspector = SceneInspector(SceneConfig(min_plane_points=50, min_object_points=12))
        with tempfile.TemporaryDirectory() as directory:
            with patch("realsense_lab.viewer.cv_module", return_value=cv):
                show(TabletopSource(3, 320, 240), Config(color_width=320, color_height=240),
                     directory, scene_inspector=inspector)
            files = list(Path(directory).glob("*.json"))
            self.assertEqual(len(files), 1)
            report = json.loads(files[0].read_text())
            self.assertEqual(len(report["objects"]), 2)
            self.assertEqual(report["frame_number"], 0)  # remained on the frozen frame
            self.assertTrue(files[0].with_suffix(".npz").exists())
            self.assertTrue(files[0].with_suffix(".ply").exists())
        self.assertEqual(cv.imshow.call_args.args[1].shape, (240, 960, 3))
        cv.destroyAllWindows.assert_called_once()

    def test_failed_reference_does_not_save_misleading_report(self):
        cv = MagicMock()
        cv.WINDOW_AUTOSIZE, cv.FONT_HERSHEY_SIMPLEX, cv.COLORMAP_TURBO = 1, 0, 20
        cv.getWindowProperty.return_value = 1
        cv.waitKey.side_effect = [ord("s"), ord("q")]
        cv.applyColorMap.side_effect = lambda image, palette: np.repeat(image[..., None], 3, axis=2)
        inspector = SceneInspector(SceneConfig(min_plane_points=100000, max_fit_points=100000))
        with tempfile.TemporaryDirectory() as directory:
            with patch("realsense_lab.viewer.cv_module", return_value=cv):
                show(TabletopSource(2, 320, 240), Config(color_width=320, color_height=240),
                     directory, scene_inspector=inspector)
            self.assertFalse(list(Path(directory).iterdir()))
