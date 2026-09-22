#!/bin/bash
set -euo pipefail
TASK_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
exec "$TASK_DIR/PDF만들기.command" "$@"
