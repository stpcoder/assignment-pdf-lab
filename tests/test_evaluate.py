import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import evaluate_gemini


class ApiRunnerTests(unittest.TestCase):
    def exercise(self, response=None, error=None):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            pdf = root / "input.pdf"
            pdf.write_bytes(b"offline-test-input")
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({"variants": [{"profile": "comment", "marker": "test_marker"}]}))
            args = ["evaluate_gemini.py", str(pdf), "--manifest", str(manifest), "--model", "offline-test-model",
                    "--mode", "pdf", "--out", str(root / "result")]
            with patch.dict(os.environ, {"GEMINI_API_KEY": "fake-offline-test-key"}), patch.object(sys, "argv", args), \
                 patch("urllib.request.urlopen", side_effect=error, return_value=io.BytesIO(json.dumps(response).encode())) as request, \
                 contextlib.redirect_stdout(io.StringIO()):
                status = evaluate_gemini.main()
            summary = json.loads((root / "result/summary.json").read_text())
            self.assertNotIn("fake-offline-test-key", json.dumps(summary))
            self.assertEqual(request.call_count, 1)
            return status, summary

    def test_success_preserves_provider_version_and_canary(self):
        status, result = self.exercise({"modelVersion": "offline-version", "candidates": [{"finishReason": "STOP", "content": {
            "parts": [{"text": "```python\n# test_marker\npass\n```"}]}}]})
        self.assertEqual(status, 0)
        self.assertEqual(result["trials"][0]["model_version"], "offline-version")
        self.assertEqual(result["trials"][0]["signal"], "canary_present_review_required")

    def test_empty_response_is_not_a_completed_trial(self):
        status, result = self.exercise({"candidates": []})
        self.assertEqual(status, 1)
        self.assertEqual(result["trials"][0]["status"], "empty_or_blocked")

    def test_http_error_is_not_a_completed_trial(self):
        status, result = self.exercise(error=urllib.error.HTTPError("https://example.invalid", 429, "rate limited", {}, None))
        self.assertEqual(status, 1)
        self.assertEqual(result["trials"][0]["http_status"], 429)


if __name__ == "__main__":
    unittest.main()
