#!/usr/bin/env bash
set -euo pipefail
TASK_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
TASK_RUNTIME_BIN="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin"
export PATH="$TASK_RUNTIME_BIN/override:$TASK_RUNTIME_BIN/fallback:/opt/homebrew/bin:/usr/local/bin:$PATH"
BUNDLED_PYTHON="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
if [[ -n "${ASSIGNMENT_PYTHON:-}" ]]; then
  TASK_PYTHON="$ASSIGNMENT_PYTHON"
elif [[ -x "$TASK_ROOT/.venv/bin/python" ]]; then
  TASK_PYTHON="$TASK_ROOT/.venv/bin/python"
elif [[ -x "$BUNDLED_PYTHON" ]]; then
  TASK_PYTHON="$BUNDLED_PYTHON"
else
  TASK_PYTHON="python3"
fi
case "${1:-}" in
  build) exec "$TASK_PYTHON" "$TASK_ROOT/preserve.py" "$@" ;;
  legacy) shift; exec "$TASK_PYTHON" "$TASK_ROOT/lab.py" "$@" ;;
  suite) shift; exec "$TASK_PYTHON" "$TASK_ROOT/signal_suite.py" "$@" ;;
  trial) shift; exec "$TASK_PYTHON" "$TASK_ROOT/trial_ledger.py" "$@" ;;
  benchmark) shift; exec "$TASK_PYTHON" "$TASK_ROOT/benchmark.py" "$@" ;;
  gemini) shift; exec "$TASK_PYTHON" "$TASK_ROOT/evaluate_gemini.py" "$@" ;;
  evidence) shift; exec "$TASK_PYTHON" "$TASK_ROOT/evidence.py" "$@" ;;
  *) exec "$TASK_PYTHON" "$TASK_ROOT/lab.py" "$@" ;;
esac
