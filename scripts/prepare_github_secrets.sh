#!/bin/bash
# 辅助脚本：准备 GitHub Secrets 所需的 JSON 字符串

echo "🔧 准备 GitHub Secrets 配置"
echo ""

# 检查 google_credentials.json 是否存在
if [ ! -f "google_credentials.json" ]; then
    echo "❌ 错误: google_credentials.json 文件不存在"
    exit 1
fi

echo "📋 Google Sheets ID:"
echo "1Cltg8pq-jhtgR6_lysW-gNIe9JSKOh2vCT4Pxo7pcpA"
echo ""

echo "📋 GOOGLE_CREDENTIALS_JSON (压缩为一行):"
python3 -c "
import json
import sys

try:
    with open('google_credentials.json', 'r') as f:
        data = json.load(f)
    
    # 压缩为一行 JSON 字符串
    json_str = json.dumps(data, separators=(',', ':'))
    print(json_str)
    print('')
    print('✅ JSON 格式正确，长度:', len(json_str), '字符')
except Exception as e:
    print(f'❌ 错误: {e}', file=sys.stderr)
    sys.exit(1)
"

echo ""
echo "📋 PRIORITY_SOURCES_LIST (可选):"
echo "nytimes.com,scmp.com,ft.com,apnews.com,washingtonpost.com,reuters.com"
echo ""
echo "💡 提示："
echo "1. 复制上面的 GOOGLE_CREDENTIALS_JSON 内容"
echo "2. 在 GitHub 仓库的 Settings → Secrets and variables → Actions 中添加"
echo "3. Secret 名称: GOOGLE_CREDENTIALS_JSON"
echo "4. Secret 值: 粘贴上面的 JSON 字符串（一行）"
echo ""
echo "✅ 完成！"

