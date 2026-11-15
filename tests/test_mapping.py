import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import numpy as np

from realsense_lab.cli import main
from realsense_lab.mapping import LocalMapper, VoxelMap
from realsense_lab.mapping_app import map_session
from realsense_lab.models import Intrinsics
from realsense_lab.odometry import MappingConfig, ProjectiveOdometry, rotation_vector, transform_points, validate_pose
from realsense_lab.room_demo import MovingRoomSource
from realsense_lab.sources import SyntheticSource


class OdometryTests(unittest.TestCase):
    def test_numerical_solver_failure_is_explicit_tracking_failure(self):
        frames = list(MovingRoomSource(2, 160, 120))
        with patch("realsense_lab.odometry.np.linalg.solve", side_effect=np.linalg.LinAlgError):
            transform, info = ProjectiveOdometry().estimate(*frames)
        self.assertIsNone(transform)
        self.assertEqual(info["reason"], "numerical_failure")

    def test_estimated_relative_pose_has_correct_direction_and_metric_scale(self):
        frames = list(MovingRoomSource(2, 320, 240))
        estimate, info = ProjectiveOdometry().estimate(*frames)
        self.assertEqual(info["reason"], "accepted")
        expected = np.linalg.inv(MovingRoomSource.pose_at(1))@MovingRoomSource.pose_at(0)
        np.testing.assert_allclose(estimate, expected, atol=.001)
        self.assertGreater(info["overlap"], .7)

    def test_single_plane_is_geometrically_degenerate(self):
        frames = list(SyntheticSource(2, 160, 120))
        for frame in frames:
            frame.depth_m[:] = 2.
        estimate, info = ProjectiveOdometry().estimate(*frames)
        self.assertIsNone(estimate)
        self.assertEqual(info["reason"], "degenerate_geometry")

    def test_no_target_depth_rejects_overlap(self):
        frames = list(MovingRoomSource(2, 160, 120))
        frames[1].depth_m[:] = 0
        estimate, info = ProjectiveOdometry().estimate(*frames)
        self.assertIsNone(estimate)
        self.assertEqual(info["reason"], "insufficient_overlap")

    def test_motion_gate_rejects_a_numerically_good_large_step(self):
        frames = list(MovingRoomSource(2, 320, 240))
        estimate, info = ProjectiveOdometry(MappingConfig(max_translation_m=.001)).estimate(*frames)
        self.assertIsNone(estimate)
        self.assertEqual(info["reason"], "motion_gate_exceeded")

    def test_distorted_geometry_is_explicitly_rejected(self):
        frame = next(iter(MovingRoomSource(1, 160, 120)))
        frame.intrinsics = Intrinsics(160, 120, 128, 128, 79.5, 59.5, "distortion.brown_conrady")
        with self.assertRaises(ValueError):
            ProjectiveOdometry().estimate(frame, frame)

    def test_pose_contract_rejects_reflection_and_nonrigid_transform(self):
        for pose in (np.diag([-1., 1, 1, 1]), np.zeros((4, 4)), np.full((4, 4), np.nan)):
            with self.assertRaises(ValueError):
                validate_pose(pose)
        rotation = rotation_vector([.1, -.2, .3])
        np.testing.assert_allclose(rotation.T@rotation, np.eye(3), atol=1e-12)


class MappingTests(unittest.TestCase):
    def test_multiframe_trajectory_against_known_poses(self):
        mapper = LocalMapper()
        entries = [mapper.update(frame) for frame in MovingRoomSource(8, 320, 240)]
        self.assertTrue(all(e["camera_to_world"] is not None for e in entries))
        for index, entry in enumerate(entries):
            np.testing.assert_allclose(entry["camera_to_world"], MovingRoomSource.pose_at(index), atol=.003)
        xyz, colors = mapper.map.cloud()
        self.assertGreater(len(xyz), 1000)
        self.assertEqual(xyz.shape, colors.shape)

    def test_world_pose_chains_inverse_relative_with_rotation(self):
        frames = list(MovingRoomSource(3, 160, 120))
        first, second = np.eye(4), np.eye(4)
        first[:3, :3], first[:3, 3] = rotation_vector([0, .05, 0]), [.02, 0, 0]
        second[:3, 3] = [0, .01, .02]
        estimator = Mock()
        estimator.estimate.side_effect = [(first, {"reason": "accepted"}), (second, {"reason": "accepted"})]
        mapper = LocalMapper(estimator=estimator)
        entries = [mapper.update(frame) for frame in frames]
        expected = np.linalg.inv(first)@np.linalg.inv(second)
        np.testing.assert_allclose(entries[-1]["camera_to_world"], expected)

    def test_failure_latches_without_fusing_or_publishing_stale_pose(self):
        frames = list(MovingRoomSource(3, 160, 120))
        estimator = Mock()
        estimator.estimate.return_value = (None, {"reason": "insufficient_overlap"})
        mapper = LocalMapper(estimator=estimator)
        mapper.update(frames[0])
        before = mapper.map.cloud()[0].copy()
        failed, next_frame = mapper.update(frames[1]), mapper.update(frames[2])
        self.assertIsNone(failed["camera_to_world"])
        self.assertEqual(next_frame["diagnostic"]["reason"], "tracking_lost_latched")
        np.testing.assert_array_equal(mapper.map.cloud()[0], before)
        estimator.estimate.assert_called_once()

    def test_clock_jump_or_domain_switch_loses_tracking(self):
        for domain in (False, True):
            frames = list(MovingRoomSource(2, 160, 120))
            mapper = LocalMapper()
            mapper.update(frames[0])
            if domain:
                frames[1].timestamp_domain = "other_clock"
            else:
                frames[1].timestamp_ms = 0
            report = mapper.update(frames[1])
            self.assertEqual(report["diagnostic"]["reason"], "timestamp_discontinuity")
            self.assertIsNone(report["camera_to_world"])

    def test_invalid_estimator_transform_is_not_integrated(self):
        frames = list(MovingRoomSource(2, 160, 120))
        for transform in (None, np.zeros((4, 4))):
            estimator = Mock()
            estimator.estimate.return_value = (transform, {"reason": "accepted"})
            mapper = LocalMapper(estimator=estimator)
            mapper.update(frames[0])
            self.assertEqual(mapper.update(frames[1])["diagnostic"]["reason"], "invalid_estimate")

    def test_voxels_average_negative_coordinates_and_color(self):
        voxel = VoxelMap(.1)
        points = np.array([[-.01, 0, 1], [-.03, 0, 1.]])
        rgb = np.array([[0, 20, 40], [100, 40, 80]], np.uint8)
        pose = np.eye(4)
        pose[0, 3] = 1.
        voxel.integrate(points, rgb, pose)
        xyz, colors = voxel.cloud()
        np.testing.assert_allclose(xyz, [[.98, 0, 1]])
        np.testing.assert_array_equal(colors, [[50, 30, 60]])

    def test_voxel_capacity_failure_is_transactional(self):
        voxel = VoxelMap(.1, 1)
        voxel.integrate(np.array([[0., 0, 1]]), np.array([[100, 0, 0]], np.uint8), np.eye(4))
        before = voxel.cloud()
        with self.assertRaises(RuntimeError):
            voxel.integrate(np.array([[0., 0, 1], [1., 0, 1]]), np.zeros((2, 3), np.uint8), np.eye(4))
        for actual, expected in zip(voxel.cloud(), before):
            np.testing.assert_array_equal(actual, expected)

    def test_manifest_contains_only_accepted_poses_and_all_frames_are_journaled(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)/"map"
            frames = list(MovingRoomSource(3, 160, 120))
            frames[1].depth_m[:] = 0
            summary = map_session(frames, target, MappingConfig(), 3)
            manifest = json.loads((target/"manifest.json").read_text())
            self.assertEqual(summary["status"], "tracking_lost")
            self.assertEqual(len(manifest["frames"]), 1)
            self.assertEqual(len((target/"tracking.jsonl").read_text().splitlines()), 3)
            self.assertEqual(len(list(target.glob("*.npz"))), 3)

    def test_mapping_session_replay_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)/"original"
            replay = Path(directory)/"replay"
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                args = ["map", "--frames", "3", "--output", str(target)]
                self.assertEqual(main(args), 0)
                self.assertEqual(main(args), 2)
                self.assertEqual(main(["map", "--source", "replay", "--input", str(target),
                                       "--frames", "3", "--output", str(replay)]), 0)
            first = json.loads((target/"trajectory.json").read_text())
            second = json.loads((replay/"trajectory.json").read_text())
            self.assertEqual(first, second)

    def test_mapping_config_rejects_bad_keys_types_and_limits(self):
        for config in ({"stride": True}, {"voxel_m": float("nan")}, {"max_voxels": 0},
                       {"min_overlap": float("nan")}, {"min_correspondences": 3}):
            with self.assertRaises(ValueError):
                MappingConfig(**config)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"config.json"
            path.write_text('{"voxl_m":0.02}')
            with self.assertRaises(ValueError):
                MappingConfig.load(path)
