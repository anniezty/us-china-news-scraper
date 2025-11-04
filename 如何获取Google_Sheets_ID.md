# 如何获取 Google Sheets ID

## 📋 什么是 Spreadsheet ID？

Spreadsheet ID 是 Google Sheets 的唯一标识符，用于程序访问特定的 Google Sheets。

## 🔍 如何获取

### 方法 1: 从 URL 中获取（最简单）

1. **打开你的 Google Sheets**
2. **查看浏览器地址栏的 URL**

URL 格式通常是：
```
https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit#gid=0
```

**SPREADSHEET_ID** 就是你需要的那部分！

### 示例

如果你的 Google Sheets URL 是：
```
https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit
```

那么 **Spreadsheet ID** 就是：
```
1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms
```

### 方法 2: 创建新的 Google Sheets

如果你还没有 Google Sheets：

1. **访问**: https://sheets.google.com
2. **创建新表格**（点击 "Blank" 或 "+"）
3. **获取 URL**（地址栏中）
4. **提取 ID**（URL 中 `/d/` 和 `/edit` 之间的部分）

## 📝 使用方式

### 在 Streamlit Cloud 中配置

1. **打开 Streamlit Cloud** → 你的应用 → Settings → Secrets
2. **添加**：
```toml
GOOGLE_SHEETS_ID = "你的-spreadsheet-id"
```

### 在代码中使用

代码会自动从环境变量或 Streamlit Secrets 读取：
```python
spreadsheet_id = os.getenv("GOOGLE_SHEETS_ID")
```

### 在网站中使用

1. 打开部署好的网站
2. 勾选 "从 Google Sheets 读取历史数据"
3. 输入 Spreadsheet ID
4. 点击 "Generate & Export"

## ⚠️ 注意事项

1. **确保 Google Sheets 已分享给 Service Account**
   - 打开 Google Sheets
   - 点击 "Share"（分享）
   - 添加 Service Account 的邮箱（从 `google_credentials.json` 中获取）
   - 给予 "Editor"（编辑者）权限

2. **Service Account 邮箱在哪里？**
   - 打开 `google_credentials.json` 文件
   - 找到 `"client_email"` 字段
   - 例如：`"us-china-picker@your-project.iam.gserviceaccount.com"`

## 🎯 快速检查清单

- [ ] 创建或打开 Google Sheets
- [ ] 从 URL 中复制 Spreadsheet ID
- [ ] 分享 Google Sheets 给 Service Account 邮箱（Editor 权限）
- [ ] 在 Streamlit Cloud Secrets 中添加 `GOOGLE_SHEETS_ID`
- [ ] 在网站中输入 Spreadsheet ID（如果需要在 UI 中配置）

## 💡 提示

如果你**暂时不需要 Google Sheets**：
- 可以使用 `app.py`（基础版本，不依赖 Google Sheets）
- 或者使用 `app_with_sheets_db.py`，但不勾选 "从 Google Sheets 读取历史数据"
- 系统会直接从 RSS 实时抓取所有数据

