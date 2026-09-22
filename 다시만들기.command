#!/bin/bash
set -euo pipefail
TASK_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
TASK_SOURCE="${1:-/Users/taehoje/Downloads/ASSN1_en_v2.docx}"
"$TASK_DIR/run.sh" build "$TASK_SOURCE" --code-font Menlo
printf '\n완료. 생성 폴더는 위 경로 또는 output/LATEST에서 확인하세요.\n'
