# 创建 Google Service Account 详细步骤

## 🎯 目标

创建一个 Service Account，用于程序访问 Google Sheets。

## 📋 完整步骤

### 第一步：打开 Google Cloud Console

1. **访问**: https://console.cloud.google.com
2. **登录**你的 Google 账号

### 第二步：创建或选择项目

1. **如果还没有项目**：
   - 点击页面顶部的项目选择器（显示当前项目名称）
   - 点击 "New Project"
   - 输入项目名称：`us-china-picker`（或你喜欢的名字）
   - 点击 "Create"

2. **如果已有项目**：
   - 点击项目选择器，选择要使用的项目

### 第三步：启用 Google Sheets API

1. **在左侧菜单**，点击 "APIs & Services" → "Library"
2. **搜索**: "Google Sheets API"
3. **点击搜索结果**
4. **点击 "Enable"**（启用）

### 第四步：创建 Service Account

1. **在左侧菜单**，点击 "APIs & Services" → "Credentials"
2. **点击页面顶部的 "+ CREATE CREDENTIALS"**
3. **选择**: "Service account"
4. **填写信息**：
   - Service account name: `us-china-picker-sa`（或你喜欢的名字）
   - Service account ID: 会自动生成（可以不改）
   - Description: `Service account for US-China news scraper`
5. **点击 "CREATE AND CONTINUE"**
6. **跳过 "Grant this service account access to project"**（点击 "CONTINUE"）
7. **跳过 "Grant users access to this service account"**（点击 "DONE"）

### 第五步：创建密钥并下载 JSON

1. **在 "Credentials" 页面**，找到刚才创建的 Service Account
2. **点击 Service Account 名称**（邮箱地址）
3. **点击 "KEYS" 标签**
4. **点击 "ADD KEY"** → "Create new key"
5. **选择 "JSON"** 格式
6. **点击 "CREATE"**
7. **JSON 文件会自动下载**（保存到你的下载文件夹）

### 第六步：重命名 JSON 文件

1. **找到下载的 JSON 文件**（通常在 Downloads 文件夹）
2. **文件名类似**: `your-project-xxxxx-xxxxx.json`
3. **重命名为**: `google_credentials.json`
4. **移动到项目目录**（可选，但建议）：
   ```bash
   mv ~/Downloads/your-project-xxxxx.json /Users/tingyuzheng/Downloads/us_china_picker/google_credentials.json
   ```

### 第七步：获取 Service Account 邮箱

1. **打开下载的 JSON 文件**
2. **找到 `"client_email"` 字段**
3. **复制邮箱地址**，例如：
   ```
   us-china-picker-sa@your-project.iam.gserviceaccount.com
   ```
4. **这个邮箱需要添加到 Google Sheets 的分享列表中**

## 🔗 快速链接

- **Google Cloud Console**: https://console.cloud.google.com
- **API Library**: https://console.cloud.google.com/apis/library
- **Credentials**: https://console.cloud.google.com/apis/credentials

## 📝 检查清单

- [ ] 创建了项目（或选择了现有项目）
- [ ] 启用了 Google Sheets API
- [ ] 创建了 Service Account
- [ ] 下载了 JSON 密钥文件
- [ ] 重命名为 `google_credentials.json`
- [ ] 复制了 Service Account 邮箱地址

## ⚠️ 注意事项

1. **JSON 文件包含敏感信息**，不要提交到 GitHub
2. **文件已在 `.gitignore` 中**，不会被意外提交
3. **Service Account 邮箱**需要添加到 Google Sheets 的分享列表

## 🎯 下一步

下载 JSON 文件后，继续：
1. 分享 Google Sheets 给 Service Account 邮箱
2. 上传 JSON 到 Streamlit Cloud Secrets（或放在本地）

