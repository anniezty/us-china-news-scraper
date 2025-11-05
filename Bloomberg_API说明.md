# Bloomberg API 集成说明

## ✅ 已完成

1. **创建了 Bloomberg 收集器** (`bloomberg_collector.py`)
   - 实现了你提供的 API 接口代码
   - 递归解析 JSON 响应提取文章
   - 支持日期过滤
   - 包含重试逻辑和错误处理

2. **集成到主收集系统** (`collector.py`)
   - 在 `collect` 函数中添加了 Bloomberg 特殊处理
   - 自动识别 Bloomberg API URL 并调用专用收集器

3. **添加到配置** (`config_en.yaml`)
   - 已添加 `bloomberg.com` 源

4. **缩写映射** (`utils.py`)
   - 已存在 Bloomberg 的缩写映射

## ⚠️ 当前问题

### 403 Forbidden 错误

Bloomberg API 返回 **403 Forbidden**，这表明：

1. **反爬虫保护**
   - Bloomberg 有严格的反爬虫机制
   - 可能需要更真实的浏览器环境（如 Selenium）
   - 或者需要特定的认证/Token

2. **可能的解决方案**

   **选项 A: 使用 Selenium（推荐）**
   ```python
   from selenium import webdriver
   from selenium.webdriver.chrome.options import Options
   
   options = Options()
   options.add_argument('--headless')
   driver = webdriver.Chrome(options=options)
   driver.get(URL)
   # 然后解析页面或 API 响应
   ```

   **选项 B: 检查是否需要 Cookie/Token**
   - 可能需要先访问主页获取 Cookie
   - 或者需要特定的 API Key

   **选项 C: 使用 RSSHub 代理（如果有）**
   - 检查 RSSHub 是否支持 Bloomberg
   - 例如：`https://rsshub.app/bloomberg/...`

   **选项 D: 使用 Google News 作为兜底**
   - 代码中已有 `site:bloomberg.com` 的 Google News 兜底
   - 虽然不是官方 API，但可以获取部分文章

## 📊 频率限制分析

### 当前状态
- ✅ 代码已实现重试逻辑（最多 3 次）
- ✅ 处理了 403、429 等错误
- ⚠️ 但由于 403 错误，无法测试实际频率限制

### 如果 API 可用
- 建议每次请求间隔 **2-3 秒**
- 如果遇到 429，等待时间递增（5秒 → 7秒 → 9秒）
- 最多重试 3 次

## 🔧 下一步建议

1. **测试 Selenium 方案**
   - 安装 `selenium` 和 `chromedriver`
   - 修改 `bloomberg_collector.py` 使用真实浏览器

2. **检查 RSSHub**
   ```bash
   # 检查 RSSHub 是否支持 Bloomberg
   curl "https://rsshub.app/bloomberg/china"
   ```

3. **使用 Google News 兜底**
   - 当前代码已配置 Google News 兜底
   - 如果 Bloomberg API 失败，会自动使用 `site:bloomberg.com` 搜索

4. **联系 Bloomberg**
   - 如果有官方 API 或 RSS 源，可以申请使用

## 📝 使用说明

即使 API 返回 403，代码已经集成完成：

- **在配置中**：`bloomberg.com` 已添加
- **在收集时**：会自动尝试 Bloomberg API
- **如果失败**：会输出错误信息，但不影响其他源
- **Google News 兜底**：如果启用，会自动使用 Google News 搜索 Bloomberg 文章

## 🎯 当前功能

代码已准备好，一旦 Bloomberg API 可用（或使用 Selenium 解决 403），就可以：
- ✅ 自动收集 Bloomberg 文章
- ✅ 按日期过滤
- ✅ 去重
- ✅ 导出到 Excel
- ✅ 上传到 Google Sheets（如果添加到优先列表）

