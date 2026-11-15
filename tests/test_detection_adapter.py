from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, Mock, patch

import numpy as np

from realsense_lab.detection import Detector
from realsense_lab.models import Frame, Intrinsics


class DetectionAdapterTests(unittest.TestCase):
    def test_masks_are_original_pixel_polygons_and_input_is_bgr(self):
        box = MagicMock()
        box.xyxy.__getitem__.return_value.cpu.return_value.numpy.return_value = np.array([5., 5., 20., 20.])
        box.cls.item.return_value, box.conf.item.return_value = 0, .9
        polygon = np.array([[5., 5.], [20., 5.], [20., 20.], [5., 20.]])
        result = SimpleNamespace(boxes=[box], masks=SimpleNamespace(xy=[polygon]), names={0: "box"})
        model = Mock()
        model.predict.return_value = [result]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"fixture.pt"
            path.write_bytes(b"fake model fixture")
            with patch.dict("sys.modules", {"ultralytics": SimpleNamespace(YOLO=Mock(return_value=model))}):
                detector = Detector(path)
        image = Frame(np.full((30, 40, 3), [10, 20, 30], np.uint8), np.ones((30, 40), np.float32),
                      Intrinsics(40, 30, 40, 40, 20, 15), 0., 0)
        observed = detector.predict(image)
        self.assertEqual(observed[0]["polygon_xy"], polygon.tolist())
        np.testing.assert_array_equal(model.predict.call_args.kwargs["source"][0, 0], [30, 20, 10])
        self.assertEqual(len(detector.metadata["weights_sha256"]), 64)
        result.boxes = None
        with self.assertRaises(RuntimeError):
            detector.predict(image)
