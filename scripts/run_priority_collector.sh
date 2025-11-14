#!/bin/bash
set -euo pipefail

export PATH="/Users/tingyuzheng/.pyenv/shims:/usr/local/bin:/usr/bin:/bin"
export GOOGLE_SHEETS_ID="1Cltg8pq-jhtgR6_lysW-gNIe9JSKOh2vCT4Pxo7pcpA"
export GOOGLE_CREDENTIALS_PATH="/Users/tingyuzheng/Projects/us_china_picker/google_credentials.json"
export PRIORITY_SOURCES_LIST="nytimes.com,scmp.com,ft.com,apnews.com,washingtonpost.com,reuters.com"
export WAPO_COOKIE_PATH="/Users/tingyuzheng/Projects/us_china_picker/.secrets/wapo_cookie.txt"
export AXIOS_COOKIE_PATH="/Users/tingyuzheng/Projects/us_china_picker/.secrets/axios_cookie.txt"

cd /Users/tingyuzheng/Projects/us_china_picker
/Users/tingyuzheng/.pyenv/versions/3.11.9/bin/python3 daily_collector_to_sheets.py


