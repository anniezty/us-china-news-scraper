# Google Sheets 作为数据库 - 工作流程说明

## ✅ 你的理解完全正确！

### 工作流程

1. **定时任务（每天运行）**
   - 抓取 NYT、SCMP、Reuters 三个优先来源当天的新闻
   - 自动上传到 Google Sheets
   - 每周创建一个新的 sheet（例如：`Week 2025-11-03`）

2. **同事访问网站生成 Excel**
   - 从 **Google Sheets** 读取 NYT、SCMP、Reuters 的历史数据
   - 从 **RSS 实时抓取** 所有其他来源的数据
   - 合并去重后生成 Excel

3. **同事在 Google Sheets 中查看**
   - 可以直接在 Google Sheets 看到三个优先来源的数据
   - 数据每天自动更新
   - 每周一个新的 sheet

## 📊 数据来源总结

### Excel 下载的数据来源

```
Excel = Google Sheets（3个优先来源） + RSS实时抓取（其他来源）
```

- **Google Sheets**: NYT、SCMP、Reuters 的历史数据
- **RSS 实时**: 所有其他来源的实时数据

### Google Sheets 中的内容

- **每周一个 sheet**: `Week 2025-11-03`、`Week 2025-11-10` 等
- **只包含 3 个优先来源**: NYT、SCMP、Reuters
- **每天自动更新**: 定时任务每天添加新文章
- **同事可以直接查看**: 无需下载 Excel

## 🔧 设置步骤

### 1. 创建 Google Sheets

1. 创建新的 Google Sheets
2. 获取 Spreadsheet ID（从 URL 中）
3. 分享给 Service Account（Editor 权限）

### 2. 设置定时任务

**修改 crontab**:
```bash
# 每天凌晨 2 点运行，上传到 Google Sheets
0 2 * * * cd /path/to/project && GOOGLE_SHEETS_ID=your-spreadsheet-id python3 daily_collector_to_sheets.py
```

或者使用环境变量文件：
```bash
# 在 .env 文件中
GOOGLE_SHEETS_ID=your-spreadsheet-id
GOOGLE_CREDENTIALS_PATH=google_credentials.json
```

### 3. 部署 Streamlit 应用

使用 `app_with_sheets_db.py` 作为主文件：
- 自动从 Google Sheets 读取历史数据
- 自动从 RSS 实时抓取
- 合并生成 Excel

## 📋 交接给同事的说明

### 给同事的文档

**使用方式**：
1. 打开网站：`https://your-app.streamlit.app`
2. 输入 Google Sheets ID（只需要输入一次，可以保存）
3. 选择日期范围
4. 点击 "Generate & Export"
5. 下载 Excel

**查看历史数据**：
- 直接打开 Google Sheets
- 可以看到每周的 sheet
- 三个优先来源的数据每天自动更新

### Google Sheets 的结构

```
Sheet 1: Week 2025-11-03
  - NYT 文章
  - SCMP 文章
  - Reuters 文章

Sheet 2: Week 2025-11-10
  - NYT 文章
  - SCMP 文章
  - Reuters 文章
...
```

## ✅ 优势

1. **数据不丢失**: 在 Google Sheets，不会因为部署而丢失
2. **同事可见**: 可以直接在 Google Sheets 查看
3. **自动更新**: 定时任务每天自动添加新数据
4. **完整数据**: Excel 包含历史数据 + 实时数据
5. **无需维护**: 云端运行，无需本地操作

## 🎯 总结

**你的理解完全正确！**

- ✅ Excel = Google Sheets（3个优先来源）+ RSS 实时（其他来源）
- ✅ 同事可以在 Google Sheets 看到三个优先来源一直在更新
- ✅ 数据在云端，不会丢失
- ✅ 交接后完全不需要你操作

