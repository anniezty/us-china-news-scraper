# 你的 Google Sheets 配置

## 📋 你的 Spreadsheet ID

从你的 URL 中提取：

**URL**: https://docs.google.com/spreadsheets/d/1Cltg8pq-jhtgR6_lysW-gNIe9JSKOh2vCT4Pxo7pcpA/edit

**Spreadsheet ID**:
```
1Cltg8pq-jhtgR6_lysW-gNIe9JSKOh2vCT4Pxo7pcpA
```

## 🔧 如何使用

### 在 Streamlit Cloud 中配置

1. **打开 Streamlit Cloud** → 你的应用 → Settings → Secrets
2. **添加**：
```toml
GOOGLE_SHEETS_ID = "1Cltg8pq-jhtgR6_lysW-gNIe9JSKOh2vCT4Pxo7pcpA"
```

### 在网站中使用

1. 打开部署好的网站
2. 勾选 "从 Google Sheets 读取历史数据"
3. 输入：`1Cltg8pq-jhtgR6_lysW-gNIe9JSKOh2vCT4Pxo7pcpA`
4. 点击 "Generate & Export"

## ⚠️ 重要：设置权限

在使用之前，必须：

1. **创建 Google Service Account**（如果还没有）
   - 访问：https://console.cloud.google.com
   - 创建项目 → 启用 Google Sheets API
   - 创建 Service Account → 下载 JSON 凭证

2. **分享 Google Sheets 给 Service Account**
   - 打开你的 Google Sheets
   - 点击右上角 "Share"（分享）
   - 添加 Service Account 的邮箱（从 `google_credentials.json` 中的 `client_email` 字段获取）
   - 给予 "Editor"（编辑者）权限

3. **上传凭证到 Streamlit Cloud**
   - 在 Streamlit Cloud Secrets 中上传 `google_credentials.json` 的内容
   - 或者使用 Secrets 格式：
```toml
[google_sheets]
credentials = '''
{
  "type": "service_account",
  "project_id": "...",
  "private_key_id": "...",
  "private_key": "...",
  "client_email": "...",
  ...
}
'''
```

## 📝 测试

配置完成后，可以测试：

```bash
# 测试上传数据
python daily_collector_to_sheets.py
```

## 🎯 总结

你的 **Spreadsheet ID**: `1Cltg8pq-jhtgR6_lysW-gNIe9JSKOh2vCT4Pxo7pcpA`

保存好这个 ID，在配置 Streamlit Cloud 和网站时会用到！

