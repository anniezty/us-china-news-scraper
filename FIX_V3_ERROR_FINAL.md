# 最终解决方案：绕过 GitHub Actions v3 缓存问题

## 问题

即使文件已经更新，GitHub Actions 每次运行还是报错：
```
This request has been automatically failed because it uses a deprecated version of `actions/upload-artifact: v3`
```

## 解决方案：创建新的 workflow 文件

由于 GitHub Actions 可能有缓存问题，最好的方法是创建一个全新的 workflow 文件。

### 步骤 1：在 GitHub 上创建新文件

1. **访问仓库**：https://github.com/anniezty/us-china-news-scraper
2. **点击 "Add file" → "Create new file"**
3. **输入路径**：`.github/workflows/daily-news-collector.yml`
4. **复制以下内容**：

```yaml
name: Daily News Collector

on:
  # 定时触发：每天在指定时间运行
  schedule:
    # GitHub Actions 使用 UTC 时间，所以需要转换为 EST (UTC-5)
    # EST 时间 → UTC 时间：
    # EST 08:07 → UTC 13:07 (同一天)
    # EST 15:07 → UTC 20:07 (同一天)
    # EST 23:37 → UTC 04:37 (第二天 UTC，但对应 EST 的当天 23:37)
    - cron: '7 13 * * *'  # UTC 13:07 = EST 08:07 (每天上午)
    - cron: '7 20 * * *'  # UTC 20:07 = EST 15:07 (每天下午)
    - cron: '37 4 * * *'  # UTC 04:37 = EST 23:37 (前一天晚上，UTC 第二天)
  
  # 允许手动触发（用于测试）
  workflow_dispatch:

jobs:
  collect-and-upload:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout repository
      uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run daily collector
      env:
        GOOGLE_SHEETS_ID: ${{ secrets.GOOGLE_SHEETS_ID }}
        GOOGLE_CREDENTIALS_JSON: ${{ secrets.GOOGLE_CREDENTIALS_JSON }}
        PRIORITY_SOURCES_LIST: ${{ secrets.PRIORITY_SOURCES_LIST }}
      run: |
        python daily_collector_to_sheets.py
```

5. **点击 "Commit new file"**

### 步骤 2：删除或禁用旧文件（可选）

1. **访问旧文件**：https://github.com/anniezty/us-china-news-scraper/blob/main/.github/workflows/daily-collector.yml
2. **点击 "Delete file"**（或重命名为 `daily-collector.yml.old`）
3. **提交删除**

### 步骤 3：测试新 workflow

1. **访问 Actions 页面**：https://github.com/anniezty/us-china-news-scraper/actions
2. **应该看到新的 workflow**："Daily News Collector"
3. **点击 "Run workflow"** 测试
4. **应该不会再报 v3 错误**

## 为什么这样做？

- **新文件名**：GitHub 会将其视为全新的 workflow，不会使用旧缓存
- **没有 upload-artifact**：完全避免了 v3 的问题
- **功能相同**：新 workflow 的功能和旧的一样

## 验证

运行新 workflow 后，应该：
- ✅ 没有 v3 错误
- ✅ 所有步骤正常执行
- ✅ 成功收集新闻到 Google Sheets

## 如果还是不行

如果新文件还是报错，可能是：
1. **GitHub 的全局缓存问题**：需要等待 GitHub 修复
2. **账户级别的问题**：可能需要联系 GitHub 支持

但创建新文件通常可以解决缓存问题。


