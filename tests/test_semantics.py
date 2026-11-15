import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

import numpy as np

from realsense_lab.cli import main
from realsense_lab.mapping_app import map_session
from realsense_lab.models import Frame, Intrinsics
from realsense_lab.odometry import MappingConfig, rotation_vector
from realsense_lab.semantic_app import SemanticSession
from realsense_lab.semantic_geometry import SemanticConfig, localize_detections
from realsense_lab.semantic_map import SemanticMap, query_objects
from realsense_lab.semantic_sources import DemoDetector, RecordedDetector, frame_fingerprint
from realsense_lab.room_demo import MovingRoomSource


def frame(number=0):
    return Frame(np.full((30, 40, 3), [10, 20, 30], np.uint8), np.ones((30, 40), np.float32),
                 Intrinsics(40, 30, 40, 40, 20, 15), number*33., number)


def detection(label="box", box=(10, 10, 20, 20), confidence=.9, **extra):
    return dict(label=label, xyxy=list(box), confidence=confidence, **extra)


def config(**changes):
    return SemanticConfig(**dict({"stride": 1, "min_points": 4, "box_margin": 0., "min_observations": 2}, **changes))


class SemanticGeometryTests(unittest.TestCase):
    def test_world_position_uses_full_rigid_transform(self):
        pose = np.eye(4)
        pose[:3, :3] = rotation_vector([0, 0, np.pi/2])
        pose[:3, 3] = [1, 2, 3]
        observed, rejected = localize_detections(frame(), [detection()], pose, config())
        self.assertFalse(rejected)
        np.testing.assert_allclose(observed[0]["xyz_camera_m"], [-.1375, -.0125, 1.])
        np.testing.assert_allclose(observed[0]["xyz_world_m"], [1.0125, 1.8625, 4.])

    def test_polygon_excludes_background_inside_the_box(self):
        image = frame()
        image.depth_m[:] = 2
        image.depth_m[10:20, 10:15] = 1
        item = detection(polygon_xy=[[10, 10], [15, 10], [15, 20], [10, 20]])
        observed, rejected = localize_detections(image, [item], np.eye(4), config())
        self.assertFalse(rejected)
        self.assertEqual(observed[0]["xyz_camera_m"][2], 1.)
        self.assertEqual(observed[0]["localization"], "polygon_depth")

    def test_no_depth_rejects_observation_instead_of_zero_position(self):
        image = frame()
        image.depth_m[:] = 0
        observed, rejected = localize_detections(image, [detection()], np.eye(4), config())
        self.assertFalse(observed)
        self.assertEqual(rejected[0]["reason"], "insufficient_depth")

    def test_mixed_depth_is_rejected(self):
        image = frame()
        image.depth_m[10:20, 10:15] = 2
        observed, rejected = localize_detections(image, [detection()], np.eye(4), config())
        self.assertFalse(observed)
        self.assertEqual(rejected[0]["reason"], "mixed_depth")

    def test_low_confidence_excluded_and_duplicate_detection(self):
        items = [detection(confidence=.2), detection("person"), detection(confidence=.8), detection(confidence=.9)]
        observed, rejected = localize_detections(frame(), items, np.eye(4), config())
        self.assertEqual(len(observed), 1)
        self.assertEqual(observed[0]["detection_index"], 3)
        self.assertEqual({r["reason"] for r in rejected}, {"low_confidence", "excluded_label", "duplicate_detection"})

    def test_malformed_detection_does_not_break_other_observations(self):
        items = [detection(box=(20, 10, 10, 20)), detection(confidence=float("nan")), detection()]
        observed, rejected = localize_detections(frame(), items, np.eye(4), config())
        self.assertEqual(len(observed), 1)
        self.assertEqual(len(rejected), 2)

    def test_invalid_pose_is_never_used(self):
        with self.assertRaises(ValueError):
            localize_detections(frame(), [detection()], np.zeros((4, 4)), config())

    def test_config_types_and_ranges(self):
        for changes in ({"stride": True}, {"box_margin": .5}, {"confidence": float("nan")},
                        {"history_limit": 0}, {"excluded_labels": "person"}):
            with self.assertRaises(ValueError):
                config(**changes)


class SemanticFusionTests(unittest.TestCase):
    def test_camera_motion_same_world_object_merges_and_confirms(self):
        objects = SemanticMap(config())
        first = objects.update(frame(0), [detection()], np.eye(4), "first.npz")
        pose = np.eye(4)
        pose[0, 3] = .1
        second = objects.update(frame(1), [detection(box=(6, 10, 16, 20))], pose, "second.npz")
        self.assertEqual(first["observations"][0]["object_id"], second["observations"][0]["object_id"])
        report = objects.report()["objects"]
        self.assertEqual(len(report), 1)
        self.assertEqual(report[0]["status"], "confirmed")
        np.testing.assert_allclose(report[0]["position_scatter_m2"], 0, atol=1e-15)
        self.assertEqual(report[0]["recent_observations"][1]["file"], "second.npz")

    def test_same_class_nearby_objects_remain_one_to_one(self):
        objects = SemanticMap(config(association_m=.5))
        items = [detection(box=(2, 10, 10, 20)), detection(box=(25, 10, 33, 20))]
        first = objects.update(frame(0), items, np.eye(4), "a.npz")
        second = objects.update(frame(1), items[::-1], np.eye(4), "b.npz")
        self.assertEqual(len(objects.report()["objects"]), 2)
        ids = [r["object_id"] for r in second["observations"]]
        self.assertEqual(len(set(ids)), 2)
        self.assertEqual(ids, [r["object_id"] for r in first["observations"]][::-1])

    def test_class_gate_and_distance_gate_do_not_merge(self):
        objects = SemanticMap(config(association_m=.1))
        objects.update(frame(0), [detection()], np.eye(4), "a.npz")
        objects.update(frame(1), [detection("chair")], np.eye(4), "b.npz")
        objects.update(frame(2), [detection(box=(25, 10, 35, 20))], np.eye(4), "c.npz")
        self.assertEqual(len(objects.report()["objects"]), 3)

    def test_duplicate_frame_does_not_inflate_confirmation(self):
        objects = SemanticMap(config())
        objects.update(frame(), [detection()], np.eye(4), "a.npz")
        with self.assertRaises(ValueError):
            objects.update(frame(), [detection()], np.eye(4), "b.npz")
        self.assertEqual(objects.report()["objects"][0]["observation_count"], 1)

    def test_history_is_bounded_but_total_and_first_seen_are_preserved(self):
        objects = SemanticMap(config(history_limit=2))
        for index in range(5):
            objects.update(frame(index), [detection()], np.eye(4), f"{index}.npz")
        item = objects.report()["objects"][0]
        self.assertEqual(item["observation_count"], 5)
        self.assertEqual(len(item["recent_observations"]), 2)
        self.assertEqual(item["first_seen"]["frame_number"], 0)
        item["recent_observations"][0]["label"] = "modified"
        self.assertEqual(objects.report()["objects"][0]["recent_observations"][0]["label"], "box")

    def test_capacity_is_reported_and_existing_landmark_still_updates(self):
        objects = SemanticMap(config(max_landmarks=1))
        objects.update(frame(0), [detection()], np.eye(4), "a.npz")
        result = objects.update(frame(1), [detection(), detection("chair")], np.eye(4), "b.npz")
        self.assertEqual(len(objects.report()["objects"]), 1)
        self.assertEqual(result["rejected"][0]["reason"], "landmark_capacity")
        self.assertEqual(objects.report()["objects"][0]["observation_count"], 2)

    def test_query_label_confirmation_and_count(self):
        objects = SemanticMap(config())
        objects.update(frame(0), [detection()], np.eye(4), "a.npz")
        self.assertFalse(query_objects(objects.report(), confirmed_only=True))
        objects.update(frame(1), [detection()], np.eye(4), "b.npz")
        self.assertEqual(len(query_objects(objects.report(), "BOX", 2, True)), 1)
        self.assertFalse(query_objects(objects.report(), "chair"))


class SemanticSessionTests(unittest.TestCase):
    def test_full_mapping_loss_exports_only_existing_semantic_observations(self):
        frames = list(MovingRoomSource(3, 320, 240))
        frames[1].depth_m[:] = 0
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)/"partial"
            summary = map_session(frames, target, MappingConfig(), 3,
                                  semantic=SemanticSession(DemoDetector()))
            report = json.loads((target/"semantic_map.json").read_text())
            journal = [json.loads(row) for row in (target/"detections.jsonl").read_text().splitlines()]
            self.assertEqual(summary["status"], "tracking_lost")
            self.assertEqual(report["mapping_status"], "tracking_lost")
            self.assertEqual(report["accepted_observations"], 2)
            self.assertTrue(all(obj["observation_count"] == 1 for obj in report["objects"]))
            self.assertTrue(journal[1]["inference_skipped"])
            self.assertTrue(journal[2]["inference_skipped"])

    def test_no_semantic_fusion_without_an_accepted_pose(self):
        detector = Mock()
        detector.metadata = {"backend": "test"}
        detector.predict.return_value = [detection()]
        session = SemanticSession(detector, config())
        with tempfile.TemporaryDirectory() as directory:
            session.start(directory)
            session.process(frame(0), {"camera_to_world": np.eye(4).tolist()}, "a.npz")
            result = session.process(frame(1), {"camera_to_world": None}, "b.npz")
            session.close()
            summary = session.finish("tracking_lost")
            self.assertEqual(summary["observations"], 1)
            self.assertEqual(result["rejected"][0]["reason"], "pose_unavailable")
            detector.predict.assert_called_once()

    def test_recorded_detections_require_identity_and_unchanged_pixels(self):
        image = frame()
        record = {"detection_schema": 1, "detections": [detection()], "frame_number": 0,
                  "timestamp_ms": 0., "timestamp_domain": "synthetic", "frame_sha256": frame_fingerprint(image)}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"detections.jsonl"
            path.write_text(json.dumps(record)+"\n")
            detector = RecordedDetector(path)
            self.assertEqual(detector.predict(image), [detection()])
            image.color[0, 0] = 0
            with self.assertRaisesRegex(ValueError, "contents"):
                detector.predict(image)
            with self.assertRaisesRegex(ValueError, "identity"):
                detector.predict(frame(1))
            path.write_text((json.dumps(record)+"\n")*2)
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                RecordedDetector(path)
            record["inference_skipped"] = True
            path.write_text(json.dumps(record)+"\n")
            with self.assertRaisesRegex(ValueError, "skipped"):
                RecordedDetector(path).predict(frame())

    def test_semantic_demo_replay_and_query_without_a_model(self):
        with tempfile.TemporaryDirectory() as directory:
            original, replay = Path(directory)/"original", Path(directory)/"replay"
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(["map", "--semantic", "--frames", "4", "--output", str(original)]), 0)
                self.assertEqual(main(["map", "--semantic", "--source", "replay", "--input", str(original),
                                       "--frames", "4", "--output", str(replay)]), 0)
                self.assertEqual(main(["objects", "--input", str(original/"semantic_map.json"), "--confirmed",
                                       "--output", str(Path(directory)/"query.json")]), 0)
            first = json.loads((original/"semantic_map.json").read_text())
            second = json.loads((replay/"semantic_map.json").read_text())
            self.assertEqual(first["objects"], second["objects"])
            self.assertEqual(len(first["objects"]), 2)
            self.assertTrue(all(o["status"] == "confirmed" for o in first["objects"]))
            self.assertEqual(json.loads((Path(directory)/"query.json").read_text())["count"], 2)
            for file in ("objects.csv", "objects.ply", "detections.jsonl", "observations.jsonl"):
                self.assertTrue((original/file).exists())

    def test_semantic_flags_require_explicit_mode(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(["map", "--weights", "model.pt", "--output", "unused"]), 2)
