import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from realsense_lab.config import Config
from realsense_lab.sources import ReplaySource, SyntheticSource
from realsense_lab.storage import load_frame, save_frame, write_json, write_ply


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.frame = next(iter(SyntheticSource(1, 32, 24)))

    def test_snapshot_roundtrip_preserves_geometry_and_color(self):
        target = self.path/"a.npz"
        save_frame(target, self.frame)
        loaded = load_frame(target)
        self.assertEqual(loaded.intrinsics, self.frame.intrinsics)
        self.assertEqual(loaded.timestamp_domain, "synthetic")
        np.testing.assert_array_equal(loaded.color, self.frame.color)
        np.testing.assert_array_equal(loaded.depth_m, self.frame.depth_m)

    def test_ray_roundtrip(self):
        self.frame.rays = np.ones((24, 32, 3), np.float32)
        save_frame(self.path/"r.npz", self.frame)
        np.testing.assert_array_equal(load_frame(self.path/"r.npz").rays, self.frame.rays)

    def test_outputs_never_overwrite(self):
        save_frame(self.path/"a.npz", self.frame)
        before = (self.path/"a.npz").read_bytes()
        with self.assertRaises(FileExistsError):
            save_frame(self.path/"a.npz", self.frame)
        self.assertEqual((self.path/"a.npz").read_bytes(), before)
        write_json(self.path/"a.json", {"ok": True})
        with self.assertRaises(FileExistsError):
            write_json(self.path/"a.json", {})

    def test_snapshot_schema_rejected(self):
        np.savez(self.path/"bad.npz", metadata=json.dumps({"schema": 999}))
        with self.assertRaises(ValueError):
            load_frame(self.path/"bad.npz")

    def test_replay_is_sorted_and_empty_is_error(self):
        with self.assertRaises(ValueError):
            ReplaySource(self.path)
        save_frame(self.path/"frame_000001.npz", self.frame)
        self.frame.number = 5
        save_frame(self.path/"frame_000002.npz", self.frame)
        with ReplaySource(self.path) as source:
            self.assertEqual([f.number for f in source], [0, 5])

    def test_synthetic_source_is_deterministic(self):
        second = next(iter(SyntheticSource(1, 32, 24)))
        np.testing.assert_array_equal(self.frame.depth_m, second.depth_m)
        self.assertTrue((self.frame.depth_m == 0).any())

    def test_ply_header_and_rgb(self):
        write_ply(self.path/"a.ply", np.array([[1., 2., 3.]]), np.array([[255, 10, 0]], np.uint8))
        content = (self.path/"a.ply").read_text()
        self.assertIn("element vertex 1", content)
        self.assertIn("1.0000000 2.0000000 3.0000000 255 10 0", content)

    def test_config_unknown_and_wrong_types_rejected(self):
        for value in ({"spatiaal": True}, {"fps": 0}, {"spatial": "true"},
                      {"max_depth_m": .1}, {"min_depth_m": float("nan")}, []):
            (self.path/"config.json").write_text(json.dumps(value))
            with self.assertRaises(ValueError):
                Config.load(str(self.path/"config.json"))
