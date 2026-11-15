import unittest
from unittest.mock import MagicMock, patch

import numpy as np

from realsense_lab.config import Config
from realsense_lab.sdk import CameraSource


class SDKBoundaryTests(unittest.TestCase):
    def test_unresolvable_profile_does_not_start(self):
        rs = MagicMock()
        rs.config.return_value.can_resolve.return_value = False
        with patch("realsense_lab.sdk.sdk", return_value=rs):
            with self.assertRaises(RuntimeError):
                with CameraSource(Config()):
                    pass
        rs.pipeline.return_value.start.assert_not_called()

    def test_partial_initialization_stops_pipeline(self):
        rs = MagicMock()
        pipe = rs.pipeline.return_value
        pipe.start.return_value.get_device.side_effect = RuntimeError("device lost")
        with patch("realsense_lab.sdk.sdk", return_value=rs):
            with self.assertRaises(RuntimeError):
                with CameraSource(Config()):
                    pass
        pipe.stop.assert_called_once()

    def test_processing_failure_closes_camera(self):
        rs = MagicMock()
        with patch("realsense_lab.sdk.sdk", return_value=rs):
            with self.assertRaises(ValueError):
                with CameraSource(Config()):
                    raise ValueError("processing failed")
        rs.pipeline.return_value.stop.assert_called_once()

    def test_native_replay_and_record_mutually_exclusive(self):
        with self.assertRaises(ValueError):
            CameraSource(Config(), playback="in.bag", record="out.bag")

    def test_meter_scaling_and_frame_identity(self):
        rs = MagicMock()
        pipe = rs.pipeline.return_value
        pipe.start.return_value.get_device.return_value.first_depth_sensor.return_value.get_depth_scale.return_value = .001
        frames = rs.align.return_value.process.return_value
        depth, color = frames.get_depth_frame.return_value, frames.get_color_frame.return_value
        depth.as_depth_frame.return_value = depth
        color.profile.format.return_value = rs.format.rgb8
        depth.get_data.return_value = np.full((6, 8), 1200, np.uint16)
        color.get_data.return_value = np.full((6, 8, 3), 200, np.uint8)
        depth.get_frame_number.return_value, depth.get_timestamp.return_value = 42, 1234.
        k = depth.profile.as_video_stream_profile.return_value.get_intrinsics.return_value
        k.width, k.height, k.fx, k.fy, k.ppx, k.ppy = 8, 6, 4., 4., 3., 2.
        k.model, k.coeffs = "distortion.none", [0.]*5
        rs.distortion.none = "distortion.none"
        source = CameraSource(Config(), count=1)
        with patch("realsense_lab.sdk.sdk", return_value=rs):
            with source:
                with patch.object(source, "_filter", side_effect=lambda d: d):
                    frame = next(iter(source))
        np.testing.assert_allclose(frame.depth_m, 1.2)
        self.assertEqual(frame.number, 42)
        self.assertEqual(frame.timestamp_ms, 1234.)
        self.assertIsNone(frame.rays)
        pipe.stop.assert_called_once()
