import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import lab


class CanaryTests(unittest.TestCase):
    def setUp(self):
        self.marker = "stair_local_variable_123456789abc"
        self.manifest = {"variants": [{"profile": "local-variable", "marker": self.marker}]}

    def test_clean_ai_and_human_code_are_both_undetermined(self):
        result = lab.scan_text("def update_position(p, m):\n    return max(0, p-m)\n", self.manifest)
        self.assertEqual(result["signal"], "no_canary_observed")
        self.assertEqual(result["authorship"], "undetermined")

    def test_identifier_detected_in_code(self):
        text = f"def f():\n    {self.marker} = 3\n    return {self.marker}\n"
        result = lab.scan_text(text, self.manifest)
        self.assertEqual(result["findings"][0]["contexts"], ["python_identifier"])
        self.assertEqual(result["findings"][0]["lines"], [2, 3])

    def test_marker_quoted_in_discussion_is_not_code_evidence(self):
        result = lab.scan_text(f"The PDF contains {self.marker}; what does it mean?", self.manifest)
        self.assertEqual(result["findings"][0]["contexts"], ["text_or_string_only"])
        self.assertEqual(result["authorship"], "undetermined")

    def test_comment_is_distinguished(self):
        result = lab.scan_text(f"# {self.marker}\nx = 3\n", self.manifest)
        self.assertEqual(result["findings"][0]["contexts"], ["python_comment"])

    def test_similar_identifier_does_not_match(self):
        result = lab.scan_text(f"{self.marker}_different = 3", self.manifest)
        self.assertEqual(result["findings"], [])

    def test_fenced_response(self):
        result = lab.scan_text(f"Here is code:\n```python\n{self.marker} = 3\n```\n", self.manifest)
        self.assertTrue(result["python_parsed"])
        self.assertEqual(result["findings"][0]["contexts"], ["python_identifier"])

    def test_scanner_never_executes_input(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "MUST_NOT_EXIST"
            text = f"from pathlib import Path\nPath({str(target)!r}).write_text('bad')\n# {self.marker}\n"
            lab.scan_text(text, self.manifest)
            self.assertFalse(target.exists())

    def test_invalid_python_still_scans(self):
        result = lab.scan_text(f"broken(\n# {self.marker}\n", self.manifest)
        self.assertFalse(result["python_parsed"])
        self.assertEqual(result["signal"], "canary_present_review_required")

    def test_layers_survive_extraction_and_do_not_change_pixels(self):
        from reportlab.pdfgen import canvas
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            baseline = temp / "baseline.pdf"
            c = canvas.Canvas(str(baseline))
            c.drawString(72, 720, "Visible assignment stays exactly the same.")
            c.save()
            base_pages = lab.render(baseline, temp / "base")
            for scheme in ("white", "invisible"):
                target = temp / (scheme + ".pdf")
                lab.inject(baseline, target, lab.payload("local-variable", self.marker), scheme)
                self.assertTrue(lab.compare_pages(base_pages, lab.render(target, temp / scheme))["identical"])
                for path in lab.extract(target, temp / (scheme + "-text")).values():
                    self.assertIn(self.marker, path.read_text())


if __name__ == "__main__":
    unittest.main()
