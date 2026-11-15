import csv
from pathlib import Path
import tempfile
import unittest

from realsense_lab.analysis import frame_health, summarize
from realsense_lab.imu import summarize_imu
from realsense_lab.sources import SyntheticSource
from realsense_lab.tracking import Tracker


def detection(x=0., label="box"):
    return {"label": label, "xyz_m": [x, 0., 2.]}


class TrackingAnalysisTests(unittest.TestCase):
    def test_association_and_metric_velocity(self):
        tracker = Tracker()
        first = tracker.update([detection()], 0)[0]
        second = tracker.update([detection(.1)], 100)[0]
        self.assertEqual(first["track_id"], second["track_id"])
        self.assertAlmostEqual(second["velocity_m_s"][0], 1.)

    def test_gating_label_and_one_to_one(self):
        tracker = Tracker()
        first = tracker.update([detection()], 0)[0]["track_id"]
        items = tracker.update([detection(.1), detection(.2), detection(2.), detection(.1, "person")], 100)
        ids = [item["track_id"] for item in items]
        self.assertEqual(ids[0], first)
        self.assertEqual(len(ids), len(set(ids)))

    def test_unknown_depth_is_not_zero_distance(self):
        tracker = Tracker()
        items = tracker.update([{"label": "box", "xyz_m": None}], 1)
        self.assertNotIn("track_id", items[0])

    def test_track_expiry_and_clock_reset(self):
        tracker = Tracker(max_missed=1)
        old_id = tracker.update([detection()], 10)[0]["track_id"]
        tracker.update([], 20)
        tracker.update([], 30)
        self.assertFalse(tracker.tracks)
        tracker.update([detection()], 40)
        new = tracker.update([detection()], 0)[0]
        self.assertNotEqual(old_id, new["track_id"])
        self.assertIsNone(new["velocity_m_s"])

    def test_gap_and_clock_reporting(self):
        result = frame_health([1, 2, 5, 1], [0, 33, 66, 0], ["hardware"]*4, 2)
        self.assertEqual(result["observed_sequence_gaps"], 2)
        self.assertEqual(result["sequence_resets_or_duplicates"], 1)
        self.assertEqual(result["timestamp_nonpositive_steps"], 1)
        self.assertEqual(result["host_throughput_fps"], 2)

    def test_mixed_timestamp_domains_not_subtracted(self):
        result = frame_health([1, 2], [0, 100000], ["hardware", "system"], 1)
        self.assertIsNone(result["median_source_interval_ms"])

    def test_empty_depth_summary_is_valid(self):
        frame = next(iter(SyntheticSource(1, 32, 24)))
        frame.depth_m[:] = 0
        result = summarize(frame)
        self.assertEqual(result["valid_fraction"], 0)
        self.assertEqual(result["sampled_points"], 0)
        self.assertNotIn("dominant_plane", result)

    def test_stationary_imu_report(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"imu.csv"
            with path.open("w", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow(["stream", "timestamp_ms", "domain", "frame_number", "x", "y", "z"])
                writer.writerow(["stream.accel", 0, "hardware", 0, 0, -9.80665, 0])
                writer.writerow(["stream.accel", 10, "hardware", 1, 0, -9.80665, 0])
            group = summarize_imu(path)["groups"][0]
            self.assertEqual(group["median_rate_hz"], 100)
            self.assertAlmostEqual(group["mean_acceleration_norm_m_s2"], 9.80665)
