# 修复 GitHub Actions v3 弃用问题

## 问题

GitHub Actions 显示错误：
```
This request has been automatically failed because it uses a deprecated version of `actions/upload-artifact: v3`
```

## 解决方案

### 方案 1：更新到 v4（推荐）

在 GitHub 上编辑 `.github/workflows/daily-collector.yml`，将第 46 行：

```yaml
uses: actions/upload-artifact@v3
```

改为：

```yaml
uses: actions/upload-artifact@v4
```

### 方案 2：删除日志上传步骤（最简单）

如果不需要上传日志，可以直接删除或注释掉这个步骤：

```yaml
# - name: Upload logs (if any)
#   if: always()
#   uses: actions/upload-artifact@v4
#   ...
```

## 如何更新

### 在 GitHub 网页上更新：

1. 访问：https://github.com/anniezty/us-china-news-scraper/blob/main/.github/workflows/daily-collector.yml
2. 点击右上角的 "✏️ Edit" 按钮
3. 找到 `actions/upload-artifact@v3` 或 `actions/upload-artifact@v4`
4. 确保是 `@v4`（如果已经是 v4 但还是报错，可能是缓存问题）
5. 或者直接删除/注释掉整个 "Upload logs" 步骤
6. 点击 "Commit changes"

### 如果已经是 v4 但还是报错：

1. **取消当前的运行**：在 Actions 页面，点击 "Cancel workflow"
2. **重新触发**：点击 "Run workflow" 重新运行
3. **清除缓存**：GitHub 可能需要几分钟来识别更新

## 验证

更新后，重新运行 workflow，应该不会再看到 v3 的弃用警告。

