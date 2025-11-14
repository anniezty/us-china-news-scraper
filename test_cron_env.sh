#!/bin/bash
# 测试 cron 环境变量
export PATH="/Users/tingyuzheng/.pyenv/shims:$PATH"
cd /Users/tingyuzheng/Downloads/us_china_picker
export GOOGLE_SHEETS_ID="1Cltg8pq-jhtgR6_lysW-gNIe9JSKOh2vCT4Pxo7pcpA"
export GOOGLE_CREDENTIALS_PATH="/Users/tingyuzheng/Downloads/us_china_picker/google_credentials.json"

echo "[$(date)] 测试 cron 环境变量"
echo "GOOGLE_SHEETS_ID=$GOOGLE_SHEETS_ID"
echo "GOOGLE_CREDENTIALS_PATH=$GOOGLE_CREDENTIALS_PATH"
echo "PATH=$PATH"
echo ""

python3 daily_collector_to_sheets.py 2>&1 | tail -20
