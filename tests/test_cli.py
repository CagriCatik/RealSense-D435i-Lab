import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from realsense_lab.cli import main
from realsense_lab.sources import SyntheticSource


class CLITests(unittest.TestCase):
    def call(self, args):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return main(args)

    def test_capture_replay_analyze_and_export(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(self.call(["capture", "--frames", "2", "--output", str(root/"frames")]), 0)
            self.assertEqual(len(list((root/"frames").glob("*.npz"))), 2)
            self.assertEqual(self.call(["analyze", "--source", "replay", "--input", str(root/"frames"),
                                       "--pixel", "320", "240", "--output", str(root/"report.json")]), 0)
            self.assertEqual(self.call(["export", "--source", "replay", "--input", str(root/"frames"),
                                       "--output", str(root/"cloud.ply")]), 0)
            self.assertTrue((root/"cloud.ply").is_file())

    def test_core_works_without_sdk_or_gui(self):
        self.assertEqual(self.call(["benchmark", "--frames", "2"]), 0)

    def test_replay_requires_input(self):
        self.assertEqual(self.call(["analyze", "--source", "replay"]), 2)

    def test_native_record_not_allowed_with_demo(self):
        self.assertEqual(self.call(["capture", "--output", "unused", "--native-record", "bad.bag"]), 2)

    def test_source_released_on_processing_failure(self):
        source = SyntheticSource(1, 32, 24)
        with patch("realsense_lab.cli.make_source", return_value=source), \
             patch.object(SyntheticSource, "__exit__", return_value=False) as close:
            self.assertEqual(self.call(["analyze", "--pixel", "999", "999"]), 2)
            close.assert_called_once()

    def test_output_overwrite_is_error(self):
        with tempfile.TemporaryDirectory() as directory:
            args = ["capture", "--frames", "1", "--output", directory]
            self.assertEqual(self.call(args), 0)
            self.assertEqual(self.call(args), 2)
