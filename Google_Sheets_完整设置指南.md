# Google Sheets 完整设置指南

## 🎯 你需要做什么

设置 Google Sheets 集成需要 3 个步骤：

1. ✅ 创建 Service Account（下载 JSON）
2. ✅ 分享 Google Sheets 给 Service Account
3. ✅ 配置 Streamlit Cloud

## 📋 步骤 1: 创建 Service Account

### 1.1 打开 Google Cloud Console

访问：https://console.cloud.google.com

### 1.2 创建项目（如果还没有）

1. 点击页面顶部的项目选择器
2. 点击 "New Project"
3. 输入项目名称：`us-china-picker`
4. 点击 "Create"

### 1.3 启用 Google Sheets API

1. 左侧菜单：**APIs & Services** → **Library**
2. 搜索：`Google Sheets API`
3. 点击并启用（Enable）

### 1.4 创建 Service Account

1. 左侧菜单：**APIs & Services** → **Credentials**
2. 点击 **+ CREATE CREDENTIALS** → **Service account**
3. 填写：
   - Service account name: `us-china-picker-sa`
   - 其他保持默认
4. 点击 **CREATE AND CONTINUE**
5. 跳过后续步骤（直接点击 **DONE**）

### 1.5 下载 JSON 密钥

1. 在 **Credentials** 页面，找到刚创建的 Service Account
2. 点击 Service Account 名称（邮箱地址）
3. 点击 **KEYS** 标签
4. 点击 **ADD KEY** → **Create new key**
5. 选择 **JSON** 格式
6. 点击 **CREATE**
7. **JSON 文件会自动下载**

### 1.6 重命名文件

将下载的 JSON 文件重命名为：`google_credentials.json`

**文件位置**：
- 通常在：`~/Downloads/` 文件夹
- 文件名类似：`your-project-xxxxx-xxxxx.json`

### 1.7 获取 Service Account 邮箱

1. 打开下载的 JSON 文件
2. 找到 `"client_email"` 字段
3. 复制邮箱地址（需要用于下一步）

## 📋 步骤 2: 分享 Google Sheets

1. **打开你的 Google Sheets**
   - https://docs.google.com/spreadsheets/d/1Cltg8pq-jhtgR6_lysW-gNIe9JSKOh2vCT4Pxo7pcpA/edit

2. **点击右上角的 "Share"（分享）按钮**

3. **添加 Service Account 邮箱**
   - 粘贴刚才复制的 `client_email`
   - 例如：`us-china-picker-sa@your-project.iam.gserviceaccount.com`

4. **设置权限为 "Editor"（编辑者）**

5. **点击 "Send"**

## 📋 步骤 3: 配置 Streamlit Cloud

### 3.1 上传 JSON 到 Secrets

1. **打开 Streamlit Cloud** → 你的应用 → **Settings** → **Secrets**

2. **有两种方式**：

**方式 A：上传文件内容**（推荐）
```toml
[google_sheets]
credentials = '''
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "xxxxx",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "us-china-picker-sa@your-project.iam.gserviceaccount.com",
  "client_id": "xxxxx",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/..."
}
'''
```

**方式 B：使用文件路径**（如果上传了文件）
```toml
GOOGLE_SHEETS_ID = "1Cltg8pq-jhtgR6_lysW-gNIe9JSKOh2vCT4Pxo7pcpA"
```

### 3.2 添加 Spreadsheet ID

```toml
GOOGLE_SHEETS_ID = "1Cltg8pq-jhtgR6_lysW-gNIe9JSKOh2vCT4Pxo7pcpA"
```

## ✅ 完成检查

设置完成后，检查：

- [ ] Service Account 已创建
- [ ] JSON 文件已下载
- [ ] Google Sheets 已分享给 Service Account 邮箱（Editor 权限）
- [ ] Streamlit Cloud Secrets 已配置

## 🧪 测试

### 测试上传数据

```bash
# 设置环境变量
export GOOGLE_SHEETS_ID="1Cltg8pq-jhtgR6_lysW-gNIe9JSKOh2vCT4Pxo7pcpA"

# 运行测试
python daily_collector_to_sheets.py
```

应该看到：
```
✅ 成功上传 X 篇文章到 Google Sheets
```

## 📝 快速参考

**你的配置信息**：
- Spreadsheet ID: `1Cltg8pq-jhtgR6_lysW-gNIe9JSKOh2vCT4Pxo7pcpA`
- Google Sheets URL: https://docs.google.com/spreadsheets/d/1Cltg8pq-jhtgR6_lysW-gNIe9JSKOh2vCT4Pxo7pcpA/edit

## 💡 提示

如果暂时不需要 Google Sheets：
- 可以直接使用网站，系统会从 RSS 实时抓取
- 不需要配置 Service Account
- 数据会直接从 RSS 获取并生成 Excel

