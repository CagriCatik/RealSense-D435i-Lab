from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET


class DocumentationTests(unittest.TestCase):
    def test_readme_demo_svg_is_well_formed(self):
        root = Path(__file__).resolve().parents[1]
        document = ET.parse(root/"docs"/"assets"/"semantic-demo.svg")
        self.assertEqual(document.getroot().tag, "{http://www.w3.org/2000/svg}svg")

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
