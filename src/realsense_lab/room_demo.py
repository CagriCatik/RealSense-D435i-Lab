"""Deterministic ray-cast room. Ground-truth poses never enter the mapper."""
import numpy as np

from .models import Frame, Intrinsics
from .odometry import rotation_vector
from .sources import SyntheticSource


def _box_hit(origin, rays, low, high, inside=False):
    safe = np.where(np.abs(rays) > 1e-12, rays, 1e-12)
    a, b = (np.asarray(low)-origin)/safe, (np.asarray(high)-origin)/safe
    near = np.minimum(a, b).max(axis=-1)
    far = np.maximum(a, b).min(axis=-1)
    distance = far if inside else near
    return np.where((far >= np.maximum(near, 0)) & (distance > 0), distance, np.inf)


class MovingRoomSource(SyntheticSource):
    @staticmethod
    def pose_at(number):
        pose = np.eye(4)
        pose[:3, :3] = rotation_vector([0., .002*number, 0.])
        pose[:3, 3] = [.005*number, .002*np.sin(number*.2), .003*number]
        return pose

    def __iter__(self):
        w, h = self.width, self.height
        k = Intrinsics(w, h, .8*w, .8*w, (w-1)/2, (h-1)/2)
        yy, xx = np.mgrid[:h, :w]
        camera_rays = np.stack(((xx-k.ppx)/k.fx, (yy-k.ppy)/k.fy, np.ones((h, w))), axis=-1)
        for number in range(min(self.count, 61)):
            pose = self.pose_at(number)
            rays, origin = camera_rays@pose[:3, :3].T, pose[:3, 3]
            depth = _box_hit(origin, rays, [-1., -.7, -.5], [1., .7, 2.5], inside=True)
            material = np.zeros((h, w), int)
            for index, (low, high) in enumerate((([-.4, -.2, 1.4], [-.1, .3, 1.8]),
                                                 ([.35, -.3, 1.8], [.6, .35, 2.1])), 1):
                hit = _box_hit(origin, rays, low, high)
                mask = hit < depth
                depth[mask], material[mask] = hit[mask], index
            world = origin+rays*depth[..., None]
            pattern = ((np.floor(world*12).sum(axis=-1).astype(int)) % 2)*30
            color = np.empty((h, w, 3), np.uint8)
            for index, rgb in enumerate(((90, 130, 160), (200, 140, 40), (80, 170, 100))):
                mask = material == index
                color[mask] = np.array(rgb)+pattern[mask, None]
            measured = (depth+np.random.default_rng(number).normal(0, .0002, depth.shape)).astype(np.float32)
            measured[::37, ::41] = 0
            yield Frame(color, measured, k, number*1000/self.fps, number)
