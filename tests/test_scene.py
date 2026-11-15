import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from realsense_lab.cli import main
from realsense_lab.models import Frame, Intrinsics
from realsense_lab.scene import SceneConfig, SceneInspector, compare_scenes
from realsense_lab.scene_io import save_scene
from realsense_lab.scene_render import segmentation_rgb
from realsense_lab.sources import TabletopSource
from realsense_lab.storage import load_frame


def fixture(count=1):
    return TabletopSource(count, 320, 240)


def settings(**changes):
    return SceneConfig(**dict({"min_plane_points": 50, "min_object_points": 12}, **changes))


class SceneTests(unittest.TestCase):
    def setUp(self):
        self.frame = next(iter(fixture()))

    def test_known_sloped_plane_two_objects_and_heights(self):
        scene = SceneInspector(settings()).inspect(self.frame)
        self.assertEqual(scene.report["status"], "ok")
        np.testing.assert_allclose(scene.report["reference_plane"], [0, -.6, -.8, 1.2], atol=.002)
        objects = scene.report["objects"]
        self.assertEqual(len(objects), 2)
        np.testing.assert_allclose(sorted(o["height_median_m"] for o in objects), [.12, .18], atol=.002)
        self.assertGreater(scene.report["reference_inlier_fraction"], .9)
        self.assertLess(scene.report["reference_rmse_m"], .002)
        self.assertEqual(len({obj["track_id"] for obj in objects}), 2)

    def test_missing_depth_stays_unknown(self):
        self.frame.depth_m[20:60, 80:120] = 0
        scene = SceneInspector(settings()).inspect(self.frame)
        self.assertTrue((scene.labels[5:15, 20:30] == -1).all())
        image = segmentation_rgb(scene, 240, 320, 4)
        self.assertTrue((image[20:60, 80:120] == 0).all())

    def test_no_valid_depth_cannot_calibrate(self):
        self.frame.depth_m[:] = 0
        with self.assertRaisesRegex(ValueError, "Not enough"):
            SceneInspector(settings()).inspect(self.frame)

    def test_reference_lost_does_not_emit_stale_objects(self):
        inspector = SceneInspector(settings())
        inspector.inspect(self.frame)
        self.frame.depth_m[:] = 0
        scene = inspector.inspect(self.frame)
        self.assertEqual(scene.report["status"], "reference_lost")
        self.assertEqual(scene.report["objects"], [])
        self.assertIsNone(scene.report["reference_rmse_m"])

    def test_plane_not_automatically_refit_after_moving_camera(self):
        inspector = SceneInspector(settings())
        before = inspector.inspect(self.frame).report["reference_plane"]
        self.frame.depth_m *= 1.15
        report = inspector.inspect(self.frame).report
        self.assertEqual(report["reference_plane"], before)
        self.assertEqual(report["status"], "reference_lost")
        inspector.reset()
        self.assertEqual(inspector.inspect(self.frame).report["status"], "ok")

    def test_geometry_change_requires_reset(self):
        inspector = SceneInspector(settings())
        inspector.inspect(self.frame)
        self.frame.intrinsics = Intrinsics(320, 240, 300, 300, 160, 120)
        with self.assertRaisesRegex(ValueError, "geometry changed"):
            inspector.inspect(self.frame)

    def test_roi_can_select_support_and_reject_insufficient_points(self):
        with self.assertRaises(ValueError):
            SceneInspector(settings(reference_roi=(0, 0, .01, .01))).inspect(self.frame)
        scene = SceneInspector(settings(reference_roi=(0, .7, 1, 1))).inspect(self.frame)
        self.assertEqual(len(scene.report["objects"]), 2)

    def test_cluster_gate_separates_adjacent_depth_discontinuities(self):
        from realsense_lab.scene import _components
        points = np.array([[0., 0., 1.], [.01, 0, 1.], [.011, 0, 1.2], [.02, 0, 1.2]])
        cells = np.array([[0, 0], [0, 1], [0, 2], [0, 3]])
        groups = _components(points, cells, np.ones(4, bool), (1, 4), .05, 2)
        self.assertEqual([len(group) for group in groups], [2, 2])

    def test_tiny_clusters_are_rejected(self):
        scene = SceneInspector(settings(min_object_points=10000)).inspect(self.frame)
        self.assertEqual(scene.report["objects"], [])

    def test_static_track_ids_persist_across_frames(self):
        inspector = SceneInspector(settings())
        ids = [set(o["track_id"] for o in inspector.inspect(frame).report["objects"])
               for frame in fixture(3)]
        self.assertEqual(ids[0], ids[1])
        self.assertEqual(ids[1], ids[2])

    def test_baseline_matching_is_one_to_one_and_has_signed_deltas(self):
        report = SceneInspector(settings()).inspect(self.frame).report
        current = copy.deepcopy(report)
        current["objects"][0]["height_above_reference_m"] += .01
        current["objects"][0]["xyz_m"][0] += .02
        result = compare_scenes(current, report)
        self.assertEqual(len(result["matches"]), 2)
        item = next(m for m in result["matches"] if m["current_segment_id"] == 1)
        self.assertAlmostEqual(item["delta_height_m"], .01)
        self.assertAlmostEqual(item["delta_xyz_m"][0], .02)
        current["objects"].append(copy.deepcopy(current["objects"][0]))
        self.assertEqual(compare_scenes(current, report)["unmatched_current"], 1)

    def test_baseline_rejects_incompatible_geometry_plane_or_status(self):
        report = SceneInspector(settings()).inspect(self.frame).report
        for key in ("intrinsics", "reference_plane", "status"):
            baseline = copy.deepcopy(report)
            if key == "intrinsics":
                baseline[key]["fx"] += 1
            elif key == "reference_plane":
                baseline[key][3] += .1
            else:
                baseline[key] = "reference_lost"
            with self.assertRaises(ValueError):
                compare_scenes(report, baseline)

    def test_config_rejects_unknown_bad_types_and_ranges(self):
        for config in ({"stride": 0}, {"min_height_m": .001}, {"min_plane_fraction": float("nan")},
                       {"cluster_gap_m": True}, {"reference_roi": [1, 0, 0, 1]}):
            with self.assertRaises(ValueError):
                SceneConfig(**config)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"config.json"
            path.write_text('{"strdie":4}')
            with self.assertRaises(ValueError):
                SceneConfig.load(path)

    def test_paired_report_snapshot_cloud_and_replay_match(self):
        scene = SceneInspector(settings()).inspect(self.frame)
        with tempfile.TemporaryDirectory() as directory:
            stem = Path(directory)/"scene"
            save_scene(stem, self.frame, scene, True)
            report = json.loads(stem.with_suffix(".json").read_text())
            loaded = load_frame(Path(directory)/report["snapshot_file"])
            replay = SceneInspector(settings()).inspect(loaded)
            self.assertEqual(replay.report, scene.report)
            vertex_count = sum(obj["sampled_points"] for obj in report["objects"])
            self.assertIn(f"element vertex {vertex_count}", stem.with_suffix(".ply").read_text())
            with self.assertRaises(FileExistsError):
                save_scene(stem, self.frame, scene, True)

    def test_headless_cli_baseline_and_existing_session(self):
        with tempfile.TemporaryDirectory() as directory:
            session = Path(directory)/"run"
            followup = Path(directory)/"compare"
            args = ["scene", "--source", "demo", "--frames", "2", "--output", str(session), "--export-cloud"]
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(args), 0)
                self.assertEqual(main(args), 2)
                self.assertEqual(main(["scene", "--source", "replay", "--input", str(session),
                    "--baseline", str(session/"scene_000000.json"), "--output", str(followup)]), 0)
            report = json.loads((followup/"scene_000000.json").read_text())
            self.assertEqual(len(report["baseline_comparison"]["matches"]), 2)

    def test_segmentation_shape_with_partial_stride_and_odd_dimensions(self):
        frame = next(iter(TabletopSource(1, 321, 241)))
        result = SceneInspector(settings()).inspect(frame)
        rgb = segmentation_rgb(result, 241, 321, 4)
        self.assertEqual(rgb.shape, (241, 321, 3))
        self.assertEqual(rgb.dtype, np.uint8)
