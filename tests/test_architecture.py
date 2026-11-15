import ast
from pathlib import Path
import unittest


class ArchitectureTests(unittest.TestCase):
    def test_core_does_not_import_adapters(self):
        root = Path(__file__).resolve().parents[1]/"src"/"realsense_lab"
        forbidden = {"pyrealsense2", "cv2", "ultralytics", "open3d", "rclpy",
                     "sdk", "viewer", "detection", "cli", "reconstruction"}
        for name in ("models", "geometry", "storage", "analysis", "tracking", "imu", "scene", "scene_render", "odometry", "mapping", "semantic_geometry", "semantic_map"):
            tree = ast.parse((root/f"{name}.py").read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports = [alias.name.split(".")[0] for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    imports = [(node.module or "").split(".")[0]]
                else:
                    continue
                self.assertFalse(set(imports) & forbidden, f"Adapter import in {name}: {imports}")
