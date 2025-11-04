# Wired RSS 源问题排查

## ✅ 已确认正常的部分

1. **RSS 源可以访问**：`https://rsshub.app/wired/tag/china` 可以正常获取 24 条新闻
2. **日期过滤正常**：在30天范围内有12条新闻
3. **配置已添加**：`config_en.yaml` 中已添加 `wired.com`
4. **代码逻辑正常**：模拟流程可以正常收集到12条数据

## 🔍 可能的问题

### 1. Streamlit 需要重启

**问题**：配置更新后，Streamlit 可能缓存了旧的配置

**解决**：
```bash
# 停止当前 Streamlit（Ctrl+C）
# 然后重新启动
streamlit run app_with_sheets_db.py
```

### 2. 源选择器没有包含 wired.com

**检查**：在 Streamlit 网页上，确认 "Sources (whitelist)" 多选框包含了 `wired.com`

**解决**：如果默认选中了所有源，应该包含 `wired.com`

### 3. 日期范围太短

**问题**：如果选择的时间范围太短（比如最近1天），Wired 可能没有新文章

**解决**：选择更大的日期范围（比如最近7天或30天）

### 4. 数据合并时被过滤

**检查**：如果从 Google Sheets 读取了数据，合并时可能有问题

## 🧪 测试步骤

1. **重启 Streamlit**：
   ```bash
   # 停止当前 Streamlit
   # 重新启动
   streamlit run app_with_sheets_db.py
   ```

2. **在网页上测试**：
   - 选择日期范围：最近7天或30天
   - 确认 "Sources (whitelist)" 包含 `wired.com`（或选择 "Select All"）
   - 点击 "Generate & Export"
   - 查看是否有 Wired 的新闻

3. **检查控制台输出**：
   - 查看是否有错误信息
   - 查看收集到的新闻数量

## 🔧 如果仍然没有显示

运行以下命令测试：

```bash
python3 << 'EOF'
from collector import collect
from datetime import datetime, timedelta

date_to = datetime.now().strftime('%Y-%m-%d')
date_from = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

df = collect(
    "config_en.yaml", 
    date_from, 
    date_to, 
    us_china_only=False, 
    limit_sources=["wired.com"]
)

print(f"收集到 {len(df)} 条 Wired 新闻")
if len(df) > 0:
    print(df[['Headline', 'Outlet', 'Date']].head())
EOF
```

如果命令可以收集到数据，但 Streamlit 没有显示，可能是：
- Streamlit 缓存问题 → 重启 Streamlit
- 源选择器问题 → 检查多选框
- 日期范围问题 → 选择更大的范围

