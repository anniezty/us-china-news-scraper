# 测试 GitHub Actions Workflow

## 🧪 如何测试

### 方法 1：手动触发（推荐 - 最快）

1. **访问 GitHub Actions 页面**
   - 打开：https://github.com/anniezty/us-china-news-scraper/actions
   - 或点击仓库顶部的 "Actions" 标签

2. **选择 Workflow**
   - 在左侧找到 "Daily News Collector" workflow
   - 点击进入

3. **手动运行**
   - 点击右上角的 "Run workflow" 按钮
   - 选择分支（通常是 `main`）
   - 点击绿色的 "Run workflow" 按钮

4. **查看运行状态**
   - 页面会自动刷新，显示新的运行记录
   - 点击运行记录查看详细日志

### 方法 2：等待定时触发

- Workflow 会在以下时间自动运行（EST）：
  - 每天 08:07
  - 每天 15:07
  - 每天 23:37

## 📊 如何查看运行结果

### 1. 查看运行日志

1. 在 Actions 页面，点击最新的运行记录
2. 点击 "collect-and-upload" job
3. 展开各个步骤查看详细日志

### 2. 检查运行状态

- ✅ **绿色勾号**：运行成功
- ❌ **红色叉号**：运行失败
- 🟡 **黄色圆圈**：正在运行

### 3. 查看日志输出

在 "Run daily collector" 步骤中，你会看到：
- 开始抓取的时间
- 找到的文章数量
- 上传到 Google Sheets 的状态
- 任何错误信息

### 4. 检查 Google Sheets

- 打开 Google Sheets
- 查看是否有新的文章被添加
- 检查日期是否是最新的

## 🔍 常见问题排查

### 问题 1: "GOOGLE_CREDENTIALS_JSON is not set"

**原因**：GitHub Secret 未正确配置

**解决**：
1. 检查 GitHub Secrets 是否已添加
2. 确认 Secret 名称是 `GOOGLE_CREDENTIALS_JSON`（完全匹配，包括大小写）
3. 确认 JSON 格式正确（一行，无换行符）

### 问题 2: "Invalid JSON format"

**原因**：JSON 字符串格式不正确

**解决**：
1. 运行 `bash scripts/prepare_github_secrets.sh` 获取正确的 JSON
2. 确保是一行，没有换行符
3. 在 GitHub Secrets 中粘贴时，确保没有额外的空格或换行

### 问题 3: "Permission denied" 或 "Authentication failed"

**原因**：Google 凭证无效或过期

**解决**：
1. 检查 `google_credentials.json` 是否有效
2. 确认服务账号有 Google Sheets 访问权限
3. 重新生成凭证并更新 GitHub Secret

### 问题 4: "No articles found"

**原因**：可能没有找到当天的文章

**解决**：
1. 这是正常的，如果当天确实没有新文章
2. 检查日志中的日期范围
3. 确认新闻来源网站有更新

### 问题 5: Workflow 没有运行

**原因**：可能是 GitHub Actions 的延迟或限制

**解决**：
1. GitHub Actions 可能有最多 5 分钟的延迟
2. 检查 workflow 是否被禁用
3. 查看 GitHub Actions 使用情况（是否超过免费额度）

## 📝 测试检查清单

- [ ] GitHub Secrets 已配置（GOOGLE_SHEETS_ID, GOOGLE_CREDENTIALS_JSON）
- [ ] Workflow 文件已提交到 GitHub
- [ ] 手动触发测试运行
- [ ] 运行状态显示成功（绿色勾号）
- [ ] 日志中没有错误信息
- [ ] Google Sheets 有新文章被添加（如果有新文章）

## 🎯 成功标志

如果看到以下内容，说明测试成功：

1. **运行状态**：✅ 绿色勾号
2. **日志输出**：
   ```
   [2025-11-18 XX:XX:XX] 开始抓取 2025-11-18 的文章...
   来源: ['nytimes.com', 'scmp.com', ...]
   [2025-11-18 XX:XX:XX] 找到 XX 篇文章
   [2025-11-18 XX:XX:XX] 正在上传到 Google Sheets: Week 2025-11-11 to 2025-11-18...
   [2025-11-18 XX:XX:XX] ✅ 成功上传 XX 篇文章到 Google Sheets
   ```
3. **Google Sheets**：有新文章被添加

## 💡 提示

- 第一次运行可能需要 2-5 分钟
- 如果运行失败，查看日志中的错误信息
- 可以多次手动触发测试，确认稳定运行
- 测试成功后，可以禁用本地定时任务（可选）

