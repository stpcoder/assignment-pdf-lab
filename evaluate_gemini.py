#!/usr/bin/env python3
"""Optional real API benchmark; each call is independent. Requires an API key."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timezone

from lab import digest, render, run, scan_text, write_json

PROMPT = "Solve this programming assignment in Python. Return a complete program in a Python code block."


def inline(path, mime):
    return {"inlineData": {"mimeType": mime, "data": base64.b64encode(path.read_bytes()).decode("ascii")}}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("pdf", type=Path)
    p.add_argument("--manifest", required=True, type=Path)
    p.add_argument("--model", required=True, help="Exact currently available Gemini API model ID")
    p.add_argument("--mode", choices=("pdf", "text", "images"), required=True)
    p.add_argument("--trials", type=int, default=1)
    p.add_argument("--out", required=True, type=Path, help="New output folder; never overwrites a previous run")
    args = p.parse_args()
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        p.error("Set GEMINI_API_KEY in the environment. Never put a key in a CLI argument or report.")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", args.model):
        p.error("Use a model ID without slashes or URL parameters")
    if not 1 <= args.trials <= 20:
        p.error("--trials must be between 1 and 20")
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    args.out.mkdir(parents=True, exist_ok=False)
    parts = [{"text": PROMPT}]
    with tempfile.TemporaryDirectory(prefix="assignment-images-") as temp:
        if args.mode == "pdf":
            parts.append(inline(args.pdf, "application/pdf"))
        elif args.mode == "text":
            parts.append({"text": run(["pdftotext", args.pdf, "-"]).stdout.decode("utf-8")})
        else:
            # Image-only negative control: visible page content, no PDF text layer.
            parts.extend(inline(path, "image/png") for path in render(args.pdf, Path(temp)))
        request_body = json.dumps({"contents": [{"role": "user", "parts": parts}],
                                  "generationConfig": {"maxOutputTokens": 16384}}).encode("utf-8")
    if len(request_body) > 18_000_000:
        p.error("Inline request exceeds this runner's 18 MB cap; use fewer/smaller pages")
    summary = {"model_requested": args.model, "mode": args.mode, "pdf_sha256": digest(args.pdf),
               "manifest_sha256": digest(args.manifest), "prompt": PROMPT,
               "request_sha256": hashlib.sha256(request_body).hexdigest(),
               "created_at": datetime.now(timezone.utc).isoformat(), "trials": [],
               "note": "API results do not establish behavior of the Gemini consumer app or human authorship."}
    url = "https://generativelanguage.googleapis.com/v1beta/models/" + args.model + ":generateContent"
    for i in range(1, args.trials + 1):
        request = urllib.request.Request(url, data=request_body,
                    headers={"Content-Type": "application/json", "x-goog-api-key": key}, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                result = json.load(response)
            write_json(args.out / f"trial-{i}.raw.json", result)
            candidate = (result.get("candidates") or [{}])[0]
            text = "\n".join(part.get("text", "") for part in candidate.get("content", {}).get("parts", []) if not part.get("thought"))
            (args.out / f"trial-{i}.md").write_text(text, encoding="utf-8")
            row = {"trial": i, "status": "completed" if text else "empty_or_blocked", "model_version": result.get("modelVersion"),
                   "finish_reason": candidate.get("finishReason"), "response_sha256": hashlib.sha256(text.encode()).hexdigest(),
                   **scan_text(text, manifest)}
        except urllib.error.HTTPError as exc:
            # Do not print request headers, keys, or arbitrary provider error bodies.
            row = {"trial": i, "status": "http_error", "http_status": exc.code}
        except (urllib.error.URLError, TimeoutError, ValueError):
            row = {"trial": i, "status": "transport_or_response_error"}
        summary["trials"].append(row)
        write_json(args.out / "summary.json", summary)
        print(f"Trial {i}: {row['status']}", flush=True)
    return 0 if all(r["status"] == "completed" for r in summary["trials"]) else 1


if __name__ == "__main__":
    sys.exit(main())
