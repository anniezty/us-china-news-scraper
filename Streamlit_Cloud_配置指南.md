# Streamlit Cloud 配置指南

## 🎯 目标

配置 Streamlit Cloud，让网站可以读取 Google Sheets 数据。

## 📋 步骤

### 步骤 1: 打开 Streamlit Cloud Secrets

1. 访问：https://share.streamlit.io
2. 登录你的账号
3. 找到你的应用
4. 点击 **Settings** → **Secrets**

### 步骤 2: 配置 Google Sheets

在 Secrets 编辑器中，粘贴以下内容：

```toml
# Google Sheets Spreadsheet ID
GOOGLE_SHEETS_ID = "1Cltg8pq-jhtgR6_lysW-gNIe9JSKOh2vCT4Pxo7pcpA"

# Google Service Account 凭证
[google_sheets]
credentials = '''
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "xxxxx",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "your-service-account@your-project.iam.gserviceaccount.com",
  "client_id": "xxxxx",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/..."
}
'''
```

### 步骤 3: 获取 JSON 内容

1. **打开你下载的 `google_credentials.json` 文件**
2. **复制全部内容**
3. **替换上面的 `credentials = '''...'''` 中的内容**

**示例**：
```toml
[google_sheets]
credentials = '''
{
  "type": "service_account",
  "project_id": "us-china-picker-123456",
  "private_key_id": "abc123def456",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...\n-----END PRIVATE KEY-----\n",
  "client_email": "us-china-picker-sa@us-china-picker-123456.iam.gserviceaccount.com",
  "client_id": "123456789012345678901",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/us-china-picker-sa%40us-china-picker-123456.iam.gserviceaccount.com"
}
'''
```

### 步骤 4: 保存并部署

1. 点击 **Save**
2. Streamlit Cloud 会自动重新部署应用
3. 等待部署完成（通常 1-2 分钟）

### 步骤 5: 测试

1. 打开你的网站
2. 勾选 "从 Google Sheets 读取历史数据"
3. 输入 Spreadsheet ID（如果未自动填充）
4. 点击 "Generate & Export"
5. 应该能看到 "✅ 从 Google Sheets 读取了 X 条历史数据"

---

## 🔧 可选：API 分类配置

如果你想使用 API 分类（可选），可以添加：

```toml
# API 分类配置（可选）
[api_classifier]
enabled = false
provider = "openai"  # 或 "anthropic"
api_key = "sk-..."
model = "gpt-4o-mini"  # 或 "claude-3-haiku-20240307"
```

**注意**：API 分类是可选的，默认使用正则表达式分类。

---

## ✅ 验证清单

配置完成后，检查：

- [ ] JSON 内容已正确粘贴（包含所有字段）
- [ ] `GOOGLE_SHEETS_ID` 正确
- [ ] Google Sheets 已分享给 Service Account 邮箱（Editor 权限）
- [ ] 应用已重新部署
- [ ] 网站可以成功读取 Google Sheets 数据

---

## 🐛 常见问题

### 1. "Google 凭证未找到"

**原因**：JSON 格式错误或配置不正确

**解决方案**：
- 确保 JSON 内容完整（包含所有字段）
- 确保使用三个单引号 `'''...'''` 包裹 JSON
- 检查 JSON 语法是否正确

### 2. "Permission denied"

**原因**：Google Sheets 未分享给 Service Account

**解决方案**：
1. 打开你的 Google Sheets
2. 点击 "Share"
3. 添加 Service Account 邮箱（从 JSON 中的 `client_email` 获取）
4. 设置权限为 "Editor"

### 3. "Spreadsheet ID 错误"

**原因**：ID 不正确

**解决方案**：
- 从 Google Sheets URL 中提取：`https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit`
- 确保 ID 正确粘贴到 `GOOGLE_SHEETS_ID`

---

## 📝 快速参考

**你的配置信息**：
- Spreadsheet ID: `1Cltg8pq-jhtgR6_lysW-gNIe9JSKOh2vCT4Pxo7pcpA`
- Google Sheets URL: https://docs.google.com/spreadsheets/d/1Cltg8pq-jhtgR6_lysW-gNIe9JSKOh2vCT4Pxo7pcpA/edit

**Service Account 邮箱**：
- 从 `google_credentials.json` 中的 `client_email` 字段获取

