#!/bin/bash
set -euo pipefail
TASK_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
TASK_BUNDLED="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
if [[ -x "$TASK_DIR/.venv/bin/python" ]]; then
  TASK_PYTHON="$TASK_DIR/.venv/bin/python"
elif [[ -x "$TASK_BUNDLED" ]]; then
  TASK_PYTHON="$TASK_BUNDLED"
else
  TASK_PYTHON="python3"
fi
"$TASK_PYTHON" "$TASK_DIR/launcher.py" "$@"
