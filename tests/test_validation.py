"""Protect failure cases that a successful demo checkout cannot exercise."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import validate


class LinkValidationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        with patch("validate.subprocess.check_output", return_value=b"assets/video.mp4\0"):
            self.check = validate.Checker(self.root, tracked_assets=True)

    def tearDown(self):
        self.temp.cleanup()

    def test_sparse_assets_require_a_tracked_path(self):
        self.check.reference("assets/video.mp4")
        self.assertEqual(self.check.errors, [])
        self.check.reference("assets/missing.mp4")
        self.assertTrue(self.check.errors)

    def test_missing_source_files_and_traversal_are_rejected(self):
        self.check.reference("app.js")
        self.check.reference("../outside.mp4")
        self.assertEqual(len(self.check.errors), 2)

    def test_query_strings_and_local_anchors(self):
        (self.root / "app.js").write_text("// example\n")
        self.check.reference("app.js?v=1")
        self.check.reference("#gallery", anchors={"gallery"})
        self.assertEqual(self.check.errors, [])
        self.check.reference("#absent", anchors={"gallery"})
        self.assertEqual(len(self.check.errors), 1)


class CorruptDataTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "assets").mkdir()
        with patch("validate.subprocess.check_output", return_value=b""):
            self.check = validate.Checker(self.root)
        self.check.reference = lambda *args, **kwargs: None

    def tearDown(self):
        self.temp.cleanup()

    def test_mismatched_video_timing_is_rejected(self):
        cases = validate.json_assignment(ROOT / "assets/cases.js", "FLOWTRACK_CASES")[:1]
        provenance = json.loads((ROOT / "assets/provenance.json").read_text())[:2]
        provenance[1]["web_metadata"]["streams"][0]["nb_frames"] = "1"
        (self.root / "assets/cases.js").write_text("window.FLOWTRACK_CASES = " + json.dumps(cases) + ";")
        (self.root / "assets/provenance.json").write_text(json.dumps(provenance))
        validate.validate_data(self.check)
        self.assertTrue(any("timing" in error for error in self.check.errors))
        self.assertTrue(any("metadata" in error for error in self.check.errors))

    def test_missing_provenance_is_rejected(self):
        cases = validate.json_assignment(ROOT / "assets/cases.js", "FLOWTRACK_CASES")[:1]
        (self.root / "assets/cases.js").write_text("window.FLOWTRACK_CASES = " + json.dumps(cases) + ";")
        (self.root / "assets/provenance.json").write_text("[]")
        validate.validate_data(self.check)
        self.assertEqual(sum("missing provenance" in error for error in self.check.errors), 2)
