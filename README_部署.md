# 快速部署指南（给交接同事）

## 🎯 目标

创建一个稳定的网站，让不懂代码的同事可以直接使用。

## ✅ 最简单方案：Streamlit Cloud（5 分钟部署）

### 步骤

1. **上传代码到 GitHub**
   ```bash
   # 如果还没有 GitHub 仓库
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/your-username/us-china-picker.git
   git push -u origin main
   ```

2. **部署到 Streamlit Cloud**
   - 访问 https://streamlit.io/cloud
   - 用 GitHub 登录
   - 点击 "New app"
   - 选择仓库，Main file path 填 `app_with_sheets_db.py`（推荐）或 `app.py`
   - 点击 "Deploy"
   - 等待 2-3 分钟

3. **完成！**
   - 获得一个 URL，例如：`https://us-china-picker.streamlit.app`
   - 分享给同事即可使用

### 使用方式

1. 打开网站
2. 选择日期范围
3. 点击 "Generate & Export"
4. 下载 Excel

**就这么简单！** 不需要任何代码操作。

## 📊 如果想用 Google Sheets（可选）

1. **创建 Google Service Account**
   - 访问 https://console.cloud.google.com
   - 创建项目 → 启用 Google Sheets API
   - 创建 Service Account → 下载 JSON 凭证

2. **共享 Google Sheets**
   - 打开 Google Sheets
   - 分享给 Service Account 邮箱（Editor 权限）

3. **配置**
   - 将 JSON 文件命名为 `google_credentials.json` 放在项目根目录
   - 使用 `app_with_sheets_db.py` 作为主文件部署
   - 在 Streamlit Cloud Secrets 中添加 `GOOGLE_SHEETS_ID`

## 🔧 维护

- **更新代码**：提交到 GitHub，Streamlit Cloud 自动重新部署
- **监控**：Streamlit Cloud 提供基础监控
- **无需服务器**：完全托管，无需维护

## 💰 成本

- **Streamlit Cloud**: 完全免费
- **Google Sheets**: 免费（15GB 空间）

## 📝 交接给同事

只需要告诉他们：
1. 打开网站 URL
2. 选择日期，点击按钮
3. 下载 Excel

**你离职后完全不用管！** ✅

