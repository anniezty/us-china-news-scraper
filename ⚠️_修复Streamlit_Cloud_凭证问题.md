# ⚠️ 修复 Streamlit Cloud 凭证问题

## 🐛 问题

在线网站显示错误：
```
⚠️ 无法读取 Google Sheets: Google 凭证文件不存在: google_credentials.json
```

**原因**：代码在 Streamlit Cloud 环境中无法正确读取 Streamlit Secrets。

## ✅ 已修复

已更新 `google_sheets_integration.py`，修复了 Streamlit Secrets 读取逻辑。

---

## 📋 现在需要做的

### 步骤 1: 确认 Streamlit Secrets 已配置

1. **打开 Streamlit Cloud**: https://share.streamlit.io
2. **找到你的应用** → **Settings** → **Secrets**
3. **确认有以下内容**：

```toml
GOOGLE_SHEETS_ID = "1Cltg8pq-jhtgR6_lysW-gNIe9JSKOh2vCT4Pxo7pcpA"

[google_sheets]
credentials = '''
{
  "type": "service_account",
  "project_id": "us-china-news-scraper",
  ...
  完整的 JSON 内容
  ...
}
'''
```

### 步骤 2: 推送修复后的代码

```bash
cd /Users/tingyuzheng/Downloads/us_china_picker

# 添加修改的文件
git add google_sheets_integration.py

# 提交
git commit -m "修复: Streamlit Cloud Secrets 读取逻辑"

# 推送
git push
```

### 步骤 3: 等待 Streamlit Cloud 重新部署

1. Streamlit Cloud 会自动检测代码更新
2. 开始重新部署（1-2 分钟）
3. 等待部署完成

### 步骤 4: 测试网站

1. **打开你的 Streamlit Cloud 网站**
2. **刷新页面**（清除缓存）
3. **勾选**: "从 Google Sheets 读取历史数据"
4. **输入 Spreadsheet ID**: `1Cltg8pq-jhtgR6_lysW-gNIe9JSKOh2vCT4Pxo7pcpA`
5. **点击**: "Generate & Export"

---

## ✅ 预期结果

**应该看到**：
- ✅ "📋 读取 Sheet: Week 2025-11-03"
- ✅ "✅ 从 Google Sheets 读取了 48 条历史数据"
- ✅ 不再显示 "⚠️ 无法读取 Google Sheets" 错误

---

## 🔍 如果还是不行

### 检查 1: Streamlit Secrets 配置

确保：
- `GOOGLE_SHEETS_ID` 已设置
- `[google_sheets].credentials` 包含完整的 JSON（所有字段）
- JSON 格式正确（使用三个单引号 `'''` 包裹）

### 检查 2: 代码已更新

在 Streamlit Cloud 查看部署日志，确认有最新的提交。

### 检查 3: 查看详细错误

如果还有错误，查看 Streamlit Cloud 的日志：
- Streamlit Cloud → 你的应用 → Logs
- 查看具体的错误信息

---

## 📝 快速检查清单

- [ ] Streamlit Secrets 已正确配置
- [ ] 代码已推送到 GitHub
- [ ] Streamlit Cloud 已重新部署
- [ ] 网站刷新后测试
- [ ] 不再显示凭证错误

