#!/bin/zsh
set -euo pipefail

PROJECT_ROOT="/Users/tingyuzheng/Projects/us_china_picker"
VENV_PATH="$PROJECT_ROOT/.venv/bin/activate"
WAPO_COOKIE_FILE="$PROJECT_ROOT/.secrets/wapo_cookie.txt"

cd "$PROJECT_ROOT"

if [ ! -f "$VENV_PATH" ]; then
  echo "❌ Virtualenv not found at $VENV_PATH"
  exit 1
fi

source "$VENV_PATH"

if [ -f "$WAPO_COOKIE_FILE" ]; then
  export WAPO_COOKIE_PATH="$WAPO_COOKIE_FILE"
else
  echo "⚠️  WaPo cookie file not found at $WAPO_COOKIE_FILE. Washington Post articles may be skipped."
fi

# 禁用 hot-reload 以防止文件变化导致重复执行 API 调用
streamlit run app_with_sheets_db.py --server.fileWatcherType none "$@"

