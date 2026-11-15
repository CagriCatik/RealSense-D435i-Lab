"""Optional TSDF reconstruction from known poses. This is not a SLAM backend."""
import json
from pathlib import Path

import numpy as np

from .geometry import require_pinhole
from .storage import load_frame


def integrate(manifest_path, output):
    try:
        import open3d as o3d
    except ImportError as exc:
        raise RuntimeError("Install the [scan] extra for TSDF reconstruction") from exc
    manifest_path, output = Path(manifest_path), Path(output)
    if output.exists():
        raise FileExistsError(output)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema") != 1 or not manifest.get("frames"):
        raise ValueError("Expected schema=1 and a non-empty frames list")
    volume = o3d.pipelines.integration.ScalableTSDFVolume(
        voxel_length=.01, sdf_trunc=.04,
        color_type=o3d.pipelines.integration.TSDFVolumeColorType.RGB8)
    for item in manifest["frames"]:
        frame = load_frame(manifest_path.parent / item["file"])
        require_pinhole(frame.intrinsics)
        pose = np.asarray(item["camera_to_world"], dtype=float)
        if pose.shape != (4, 4) or not np.isfinite(pose).all():
            raise ValueError("Pose must be a finite 4x4 matrix")
        rotation = pose[:3, :3]
        if (not np.allclose(pose[3], [0, 0, 0, 1])
                or not np.allclose(rotation.T @ rotation, np.eye(3), atol=1e-5)
                or not np.isclose(np.linalg.det(rotation), 1., atol=1e-5)):
            raise ValueError("Pose must be a rigid camera-to-world transform")
        depth = np.where(np.isfinite(frame.depth_m) & (frame.depth_m > 0), frame.depth_m, 0).astype(np.float32)
        rgbd = o3d.geometry.RGBDImage.create_from_color_and_depth(
            o3d.geometry.Image(np.ascontiguousarray(frame.color)),
            o3d.geometry.Image(depth), depth_scale=1., depth_trunc=3.,
            convert_rgb_to_intensity=False)
        k = frame.intrinsics
        intrinsic = o3d.camera.PinholeCameraIntrinsic(k.width, k.height, k.fx, k.fy, k.ppx, k.ppy)
        # Open3D expects world-to-camera, while our manifest declares camera-to-world.
        volume.integrate(rgbd, intrinsic, np.linalg.inv(pose))
    mesh = volume.extract_triangle_mesh()
    if not len(mesh.vertices):
        raise ValueError("TSDF contains no surface; inspect depth and poses")
    mesh.compute_vertex_normals()
    output.parent.mkdir(parents=True, exist_ok=True)
    if not o3d.io.write_triangle_mesh(str(output), mesh):
        raise RuntimeError("Open3D could not write mesh")
    return {"frames": len(manifest["frames"]), "vertices": len(mesh.vertices),
            "triangles": len(mesh.triangles), "output": str(output)}
