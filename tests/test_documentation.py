from pathlib import Path
import re
import unittest


class DocumentationTests(unittest.TestCase):
    def test_local_markdown_links_resolve(self):
        root = Path(__file__).resolve().parents[1]
        paths = [root/"README.md", root/"TUTORIAL_INDEX.md"]
        for directory in ("docs", "projects", "ros2"):
            paths.extend((root/directory).rglob("*.md"))
        for path in paths:
            text = path.read_text(encoding="utf-8")
            for target in re.findall(r"\]\(([^)]+)\)", text):
                if "://" in target or target.startswith("#"):
                    continue
                resolved = path.parent/target.split("#")[0]
                self.assertTrue(resolved.exists(), f"Broken link in {path.name}: {target}")

    def test_all_16_projects_have_tutorials(self):
        root = Path(__file__).resolve().parents[1]
        self.assertEqual(len(list((root/"projects").glob("*/TUTORIAL.md"))), 16)
