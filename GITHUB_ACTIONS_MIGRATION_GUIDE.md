# GitHub Actions 迁移指南

## 📋 概述

本指南说明如何将本地定时任务迁移到 GitHub Actions，实现完全自动化的新闻收集，无需担心电脑休眠问题。

## ✅ 优势

- ✅ **完全自动化**：无需电脑开机
- ✅ **免费**：GitHub Actions 提供 2000 分钟/月的免费额度
- ✅ **可靠**：不会因为电脑休眠而错过任务
- ✅ **可追踪**：所有运行记录都在 GitHub 上
- ✅ **易于调试**：可以直接查看日志

## 🔧 迁移步骤

### 步骤 1: 准备 Google 凭证

1. **获取 Google 凭证 JSON**
   - 打开你的 `google_credentials.json` 文件
   - 复制整个 JSON 内容

2. **验证凭证格式**
   - 确保是有效的 JSON 格式
   - 包含 `type`, `project_id`, `private_key` 等字段

### 步骤 2: 配置 GitHub Secrets

1. **打开 GitHub 仓库**
   - 访问你的仓库：https://github.com/anniezty/us-china-news-scraper

2. **进入 Settings → Secrets and variables → Actions**

3. **添加以下 Secrets**：

   #### Secret 1: `GOOGLE_SHEETS_ID`
   ```
   值: 1Cltg8pq-jhtgR6_lysW-gNIe9JSKOh2vCT4Pxo7pcpA
   ```

   #### Secret 2: `GOOGLE_CREDENTIALS_JSON`
   ```
   值: 粘贴整个 google_credentials.json 的内容（作为一行 JSON 字符串）
   ```
   
   **重要**：
   - 必须是一行 JSON 字符串
   - 不能有换行符
   - 可以使用在线工具将多行 JSON 压缩为一行：https://jsonformatter.org/json-minify

   **示例**：
   ```json
   {"type":"service_account","project_id":"us-china-news-scraper","private_key_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n","client_email":"...","client_id":"...","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"..."}
   ```

   #### Secret 3: `PRIORITY_SOURCES_LIST` (可选)
   ```
   值: nytimes.com,scmp.com,ft.com,apnews.com,washingtonpost.com,reuters.com
   ```
   
   如果不设置，将使用默认来源列表。

### 步骤 3: 验证 Workflow 文件

1. **检查 workflow 文件**
   - 文件位置：`.github/workflows/daily-collector.yml`
   - 确保文件已提交到 GitHub

2. **检查定时任务时间**
   - 当前配置使用 UTC 时间
   - EST 08:07 = UTC 13:07
   - EST 15:07 = UTC 20:07
   - EST 23:37 = UTC 04:37 (第二天)

### 步骤 4: 测试运行

1. **手动触发测试**
   - 在 GitHub 仓库页面，点击 "Actions" 标签
   - 选择 "Daily News Collector" workflow
   - 点击 "Run workflow" → "Run workflow"
   - 等待运行完成

2. **检查运行结果**
   - 查看运行日志，确认没有错误
   - 检查 Google Sheets，确认有新文章被添加

### 步骤 5: 禁用本地定时任务（可选）

如果 GitHub Actions 运行正常，可以禁用本地定时任务：

```bash
# 卸载本地定时任务
launchctl unload ~/Library/LaunchAgents/com.uschina.dailycollector.plist

# 或者只是停止，不删除配置
launchctl stop com.uschina.dailycollector
```

**建议**：先让两个任务并行运行几天，确认 GitHub Actions 稳定后再禁用本地任务。

## 📅 时区说明

### UTC vs EST 时间对照

| 本地时间 (EST) | UTC 时间 | Cron 表达式 |
|---------------|---------|------------|
| 08:07 | 13:07 | `7 13 * * *` |
| 15:07 | 20:07 | `7 20 * * *` |
| 23:37 | 04:37 (第二天) | `37 4 * * *` |

### 夏令时 (EDT) 调整

**注意**：EST 是标准时间（UTC-5），EDT 是夏令时（UTC-4）。

如果使用 EDT：
- EST 08:07 = UTC 12:07 (EDT)
- EST 15:07 = UTC 19:07 (EDT)
- EST 23:37 = UTC 03:37 (EDT，第二天)

**建议**：使用 EST 时间（UTC-5），这样更稳定，不受夏令时影响。

## 🔍 如何查看运行日志

1. **在 GitHub 上查看**
   - 访问：https://github.com/anniezty/us-china-news-scraper/actions
   - 点击最新的运行记录
   - 查看 "collect-and-upload" job 的日志

2. **下载日志文件**
   - 运行完成后，可以下载 "collector-logs" artifact
   - 包含所有日志文件

## 🐛 故障排除

### 问题 1: "GOOGLE_CREDENTIALS_JSON is not set"

**原因**：GitHub Secret 未正确配置

**解决**：
1. 检查 GitHub Secrets 是否已添加
2. 确认 JSON 格式正确（一行，无换行符）
3. 重新运行 workflow

### 问题 2: "Invalid JSON format"

**原因**：JSON 字符串格式不正确

**解决**：
1. 使用在线工具压缩 JSON：https://jsonformatter.org/json-minify
2. 确保是一行，没有换行符
3. 转义特殊字符（如 `\n` 在 private_key 中）

### 问题 3: "Permission denied" 或 "Authentication failed"

**原因**：Google 凭证无效或过期

**解决**：
1. 检查 `google_credentials.json` 是否有效
2. 确认服务账号有 Google Sheets 访问权限
3. 重新生成凭证并更新 GitHub Secret

### 问题 4: Workflow 没有按时运行

**原因**：可能是 GitHub Actions 的延迟或限制

**解决**：
1. GitHub Actions 可能有最多 5 分钟的延迟
2. 检查 workflow 是否被禁用
3. 查看 GitHub Actions 使用情况（是否超过免费额度）

### 问题 5: 时区不对

**原因**：Cron 表达式使用 UTC 时间

**解决**：
1. 根据你的时区调整 cron 表达式
2. 参考上面的时区对照表

## 📊 监控和通知

### 查看运行历史

- 访问：https://github.com/anniezty/us-china-news-scraper/actions
- 查看所有运行记录和状态

### 设置通知（可选）

可以在 workflow 中添加通知功能：

```yaml
- name: Send notification on failure
  if: failure()
  uses: actions/github-script@v6
  with:
    script: |
      github.rest.issues.create({
        owner: context.repo.owner,
        repo: context.repo.repo,
        title: 'Daily collector failed',
        body: 'The daily collector workflow failed. Please check the logs.'
      })
```

## 💰 成本说明

### GitHub Actions 免费额度

- **免费账户**：2000 分钟/月
- **Pro 账户**：3000 分钟/月

### 估算使用量

- 每次运行约 2-5 分钟
- 每天 3 次 = 6-15 分钟/天
- 每月约 180-450 分钟
- **完全在免费额度内** ✅

## 🔄 回滚方案

如果 GitHub Actions 出现问题，可以：

1. **重新启用本地定时任务**
   ```bash
   launchctl load ~/Library/LaunchAgents/com.uschina.dailycollector.plist
   ```

2. **手动运行一次**
   ```bash
   cd /Users/tingyuzheng/Projects/us_china_picker
   python3 daily_collector_to_sheets.py
   ```

## ✅ 迁移检查清单

- [ ] GitHub Secrets 已配置（GOOGLE_SHEETS_ID, GOOGLE_CREDENTIALS_JSON）
- [ ] Workflow 文件已提交到 GitHub
- [ ] 手动测试运行成功
- [ ] Google Sheets 有新文章被添加
- [ ] 确认定时任务时间正确（UTC）
- [ ] 监控几天，确认稳定运行
- [ ] （可选）禁用本地定时任务

## 🎉 完成！

迁移完成后，你的新闻收集将：
- ✅ 完全自动化，无需电脑开机
- ✅ 不会因为休眠而错过任务
- ✅ 所有运行记录都在 GitHub 上
- ✅ 易于调试和监控

## 📚 相关文档

- [自动收集说明](./AUTOMATIC_COLLECTION_EXPLAINED.md)
- [工作流程指南](./工作流程.md)

