"""Incomplete research inputs must not remove a published bundle."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import prepare_assets


class PreparationTest(unittest.TestCase):
    def test_result_selection_rejects_missing_or_ambiguous_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result_dir = root / "edit1/video"
            result_dir.mkdir(parents=True)
            with self.assertRaises(ValueError):
                prepare_assets.find_result(root, 1, "video")
            (result_dir / "one.mp4").touch()
            self.assertEqual(prepare_assets.find_result(root, 1, "video").name, "one.mp4")
            (result_dir / "two.mp4").touch()
            with self.assertRaises(ValueError):
                prepare_assets.find_result(root, 1, "video")

    def test_timing_mismatch_fails_before_removing_published_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("source", "results/edit1/video", "prompts", "code", "site/assets/videos"):
                (root / name).mkdir(parents=True)
            (root / "paper.pdf").touch()
            (root / "source/video.mp4").touch()
            (root / "results/edit1/video/one.mp4").touch()
            old = root / "site/assets/videos/old-baseline.mp4"
            old.write_bytes(b"published clip")
            (root / "prompts/flowtrack_ablation_direct_execution_edit1_existing.json").write_text(
                json.dumps([{"id": "video", "instruction": "edit", "source_prompt": "source", "target_prompt": "target"}]))
            metadata = [{"streams": [{"width": 832, "height": 480, "r_frame_rate": "16/1", "nb_frames": str(n)}],
                         "format": {"duration": "5.063"}} for n in (81, 80)]
            argv = ["prepare_assets.py", "--workspace", str(root), "--source-dir", str(root / "source"),
                    "--results-dir", str(root / "results"), "--prompts-dir", str(root / "prompts"),
                    "--paper", str(root / "paper.pdf"), "--code-dir", str(root / "code")]
            with patch.object(sys, "argv", argv), patch.object(prepare_assets, "WORKSPACE", root), \
                 patch.object(prepare_assets, "ASSETS", root / "site/assets"), \
                 patch.object(prepare_assets, "SELECTION", [("test", "video", 1, "subject", "A", "B", "edit", 1.0)]), \
                 patch.object(prepare_assets.shutil, "which", return_value="tool"), \
                 patch.object(prepare_assets, "probe", side_effect=metadata):
                with self.assertRaisesRegex(ValueError, "Unmatched"):
                    prepare_assets.main()
            self.assertEqual(old.read_bytes(), b"published clip")
