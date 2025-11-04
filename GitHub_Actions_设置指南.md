# GitHub Actions 设置指南

## 🎯 为什么使用 GitHub Actions？

- ✅ **免费**：GitHub 提供免费额度，足够使用
- ✅ **云端运行**：不占用你的电脑资源
- ✅ **可靠**：GitHub 基础设施，稳定运行
- ✅ **离职后继续**：不需要你的电脑

---

## 📋 设置步骤

### 步骤 1: 配置 GitHub Secrets

1. **打开 GitHub 仓库**：https://github.com/anniezty/us-china-news-scraper
2. **Settings** → **Secrets and variables** → **Actions**
3. **New repository secret**，添加以下两个：

#### Secret 1: `GOOGLE_SHEETS_ID`
```
名称: GOOGLE_SHEETS_ID
值: 1Cltg8pq-jhtgR6_lysW-gNIe9JSKOh2vCT4Pxo7pcpA
```

#### Secret 2: `GOOGLE_CREDENTIALS_JSON`
```
名称: GOOGLE_CREDENTIALS_JSON
值: {
  "type": "service_account",
  "project_id": "us-china-news-scraper",
  ...
  粘贴完整的 google_credentials.json 内容
  ...
}
```

**如何获取 JSON 内容**：
```bash
cat google_credentials.json
```

复制全部内容，粘贴到 Secret 值中。

---

### 步骤 2: 验证 Workflow

1. **打开 Actions 标签**：https://github.com/anniezty/us-china-news-scraper/actions
2. **应该能看到 "Daily Collector to Google Sheets" workflow**
3. **可以手动触发测试**：
   - 点击 workflow
   - 点击 "Run workflow"
   - 选择 "Run workflow"

---

### 步骤 3: 从你的电脑删除定时任务

设置完成后，从你的电脑删除 cron 任务：

```bash
# 删除所有相关任务
crontab -l | grep -v "daily_collector_to_sheets" | crontab -

# 验证已删除
crontab -l | grep daily_collector
# 应该没有输出
```

---

## ⏰ 时区说明

**注意**：GitHub Actions 使用 UTC 时间，需要转换：

- **EST 8:07** = UTC 13:07（冬季 UTC-5）
- **EST 15:07** = UTC 20:07
- **EST 23:37** = UTC 04:37（次日）

如果你们使用其他时区，需要调整：
- **EDT（夏令时）**：UTC-4，需要 +1 小时
- **PST**：UTC-8，需要 +8 小时

---

## 🔍 检查执行日志

1. **打开 Actions**：https://github.com/anniezty/us-china-news-scraper/actions
2. **点击最新的 workflow run**
3. **查看日志**，应该看到：
   - ✅ "找到 X 篇文章"
   - ✅ "成功上传 X 篇文章到 Google Sheets"

---

## ✅ 优势

1. **不占用你的资源**：完全在 GitHub 云端运行
2. **离职后继续**：不需要你的电脑
3. **自动执行**：每天 3 次自动运行
4. **免费**：GitHub 免费额度足够

---

## 🎉 完成！

设置完成后：
- ✅ 定时任务在 GitHub 云端运行
- ✅ 不占用你的电脑资源
- ✅ 离职后继续工作
- ✅ 可以从你的电脑删除 cron 任务

---

## 🆘 需要帮助？

如果设置过程中遇到问题，告诉我：
1. Secrets 配置是否正确
2. Workflow 是否运行成功
3. 日志显示什么错误

我可以帮你排查！

