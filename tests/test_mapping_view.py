import unittest
from unittest.mock import MagicMock, patch

from realsense_lab.mapping import LocalMapper
from realsense_lab.mapping_view import MapPreview
from realsense_lab.room_demo import MovingRoomSource


class MappingPreviewTests(unittest.TestCase):
    def test_lost_frame_has_no_new_trajectory_point_and_q_stops(self):
        cv = MagicMock()
        cv.FONT_HERSHEY_SIMPLEX = 0
        cv.waitKey.side_effect = [0, ord("q")]
        with patch("realsense_lab.mapping_view.cv_module", return_value=cv):
            preview = MapPreview()
        frame = next(iter(MovingRoomSource(1, 160, 120)))
        mapper = LocalMapper()
        initial = mapper.update(frame)
        self.assertTrue(preview(frame, mapper, initial))
        frame.depth_m[:] = 0
        frame.timestamp_ms += 33
        failed = mapper.update(frame)
        self.assertFalse(preview(frame, mapper, failed))
        self.assertEqual(len(preview.path), 1)
        self.assertEqual(cv.imshow.call_args.args[1].shape, (120, 320, 3))
        preview.close()
        cv.destroyAllWindows.assert_called_once()
