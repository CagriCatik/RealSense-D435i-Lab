import unittest

import numpy as np

from realsense_lab.geometry import (bounding_box, deproject, fit_plane, frame_cloud,
                                    frame_point, pointcloud, robust_depth)
from realsense_lab.models import Frame, Intrinsics


class GeometryTests(unittest.TestCase):
    def setUp(self):
        self.k = Intrinsics(8, 6, 4., 4., 3., 2.)
        self.depth = np.full((6, 8), 2., np.float32)
        self.color = np.zeros((6, 8, 3), np.uint8)

    def test_optical_axes_and_units(self):
        np.testing.assert_allclose(deproject((3, 2), 2, self.k), [0, 0, 2])
        np.testing.assert_allclose(deproject((5, 4), 2, self.k), [1, 1, 2])

    def test_invalid_geometry_rejected(self):
        for z in (0, -1, np.nan, np.inf):
            with self.assertRaises(ValueError):
                deproject((0, 0), z, self.k)
        with self.assertRaises(ValueError):
            deproject((8, 0), 2, self.k)
        with self.assertRaises(ValueError):
            Intrinsics(8, 6, 0., 4., 3., 2.)

    def test_distortion_cannot_be_silently_ignored(self):
        k = Intrinsics(8, 6, 4, 4, 3, 2, "distortion.brown_conrady")
        with self.assertRaises(ValueError):
            deproject((3, 2), 2, k)
        rays = np.zeros((6, 8, 3), np.float32)
        rays[:] = [0.5, 0.25, 1.]
        f = Frame(self.color, self.depth, k, 0., 0, rays=rays)
        np.testing.assert_allclose(frame_point(f, (3, 2))[0], [1., .5, 2.])
        xyz, _ = frame_cloud(f)
        np.testing.assert_allclose(xyz, np.tile([1., .5, 2.], (len(xyz), 1)))

    def test_depth_neighborhood_excludes_invalid_and_rejects_empty(self):
        self.depth[0, :2] = [np.nan, 0]
        self.assertEqual(robust_depth(self.depth, (0, 0), 1), (2., 0., 2))
        self.depth[:] = 0
        with self.assertRaises(ValueError):
            robust_depth(self.depth, (2, 2))

    def test_cloud_color_correspondence_and_cutoff(self):
        self.depth[0, 0], self.depth[0, 2], self.depth[0, 4] = 0, np.nan, 4
        xyz, pixels = pointcloud(self.depth, self.k, 2, 3)
        self.assertEqual(len(xyz), 9)
        for point, (y, x) in zip(xyz, pixels):
            np.testing.assert_allclose(point, deproject((x, y), self.depth[y, x], self.k))

    def test_frame_contract_rejects_misalignment(self):
        with self.assertRaises(ValueError):
            Frame(self.color, self.depth[:, :4], self.k, 0, 0)
        with self.assertRaises(ValueError):
            Frame(self.color, self.depth.astype(np.uint16), self.k, 0, 0)

    def test_plane_with_outliers(self):
        rng = np.random.default_rng(5)
        xy = rng.uniform(-1, 1, (500, 2))
        plane_points = np.c_[xy, 2+rng.normal(0, .001, 500)]
        outliers = rng.uniform(-3, 3, (100, 3))
        plane, mask = fit_plane(np.vstack((plane_points, outliers)), threshold=.01)
        np.testing.assert_allclose(plane, [0, 0, 1, -2], atol=.003)
        self.assertGreaterEqual(mask[:500].sum(), 495)
        self.assertLess(mask[500:].sum(), 5)

    def test_plane_degenerate_and_nonfinite(self):
        for p in (np.zeros((20, 3)), np.ones((2, 3)), np.full((5, 3), np.nan)):
            with self.assertRaises(ValueError):
                fit_plane(p)

    def test_bounds_are_visible_extents(self):
        result = bounding_box(np.array([[0, -1, 1], [2, 1, 3]]))
        self.assertEqual(result["visible_extent_m"], [2, 2, 2])
