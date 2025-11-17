# Streamlit Cloud API 无法使用问题排查

## 🔍 问题

**本地可以使用 API，但线上（Streamlit Cloud）无法使用**

## 📝 可能的原因

### 1. Streamlit Cloud Secrets 未正确配置（最可能）

**检查步骤**：
1. 登录 Streamlit Cloud: https://share.streamlit.io/
2. 进入你的应用
3. 点击 "Settings" → "Secrets"
4. 检查是否有 `[api]` 部分
5. 检查 `classifier_enabled` 是否为 `true`（不是字符串 `"true"`）
6. 检查 `openai_api_key` 是否正确

**正确的格式**：
```toml
[api]
classifier_enabled = true
provider = "openai"
openai_api_key = "sk-你的-API-key"
openai_model = "gpt-4o-mini"
daily_budget_usd = 1.0
cost_per_call_usd = 0.001
```

**常见错误**：
- ❌ `classifier_enabled = "true"` （字符串，应该是布尔值 `true`）
- ❌ 缺少 `openai_api_key`
- ❌ API key 格式错误（缺少 `sk-` 前缀）

### 2. Streamlit Cloud 未重新部署

**检查步骤**：
1. 确认代码已推送到 GitHub
2. 检查 Streamlit Cloud 是否自动部署
3. 如果没有自动部署，手动触发部署

### 3. API key 权限问题

**检查步骤**：
1. 确认 API key 是否有效
2. 确认 API key 是否有足够的配额
3. 确认 API key 是否被限制（某些企业账号可能有 IP 限制）

### 4. 环境变量优先级问题

**代码逻辑**：
- 优先从 Streamlit Secrets 读取
- 如果 Secrets 中没有，从环境变量读取

**可能的问题**：
- Streamlit Cloud 的环境变量可能覆盖了 Secrets
- 需要检查 Streamlit Cloud 的环境变量设置

## 🔧 诊断步骤

### 步骤 1: 检查 Streamlit Cloud Secrets

1. 登录 Streamlit Cloud
2. 进入应用设置
3. 检查 Secrets 配置

**正确的配置示例**：
```toml
[api]
classifier_enabled = true
provider = "openai"
openai_api_key = "sk-proj-..."
openai_model = "gpt-4o-mini"
daily_budget_usd = 1.0
cost_per_call_usd = 0.001
```

### 步骤 2: 检查应用日志

1. 在 Streamlit Cloud 中，点击 "Settings" → "Logs"
2. 查看 `stderr` 日志
3. 查找以下信息：
   - `🔍 is_api_available() returned: True/False`
   - `❌ API key not found`
   - `❌ API not available`

### 步骤 3: 添加调试信息

在 `app_with_sheets_db.py` 中添加调试信息，显示 API 配置状态。

## 💡 快速修复

### 方法 1: 重新配置 Streamlit Cloud Secrets

1. 登录 Streamlit Cloud
2. 进入应用 → Settings → Secrets
3. 删除旧的 `[api]` 配置
4. 添加新的配置（使用正确的格式）
5. 保存并重新部署

### 方法 2: 检查代码中的 API 检查逻辑

确保 `is_api_available()` 函数能正确读取 Streamlit Secrets。

## 📝 常见问题

### Q: 为什么本地可以，线上不行？

**A**: 可能的原因：
1. 本地使用 `.streamlit/secrets.toml`，线上使用 Streamlit Cloud Secrets
2. 配置格式不同（布尔值 vs 字符串）
3. Streamlit Cloud Secrets 未正确配置

### Q: 如何确认 API 是否可用？

**A**: 在 Streamlit UI 中：
1. 勾选 "Use API Classification"
2. 查看是否有错误信息
3. 查看日志中的调试信息

### Q: 如何查看 Streamlit Cloud 日志？

**A**: 
1. 登录 Streamlit Cloud
2. 进入应用
3. 点击 "Settings" → "Logs"
4. 查看 `stderr` 日志（包含调试信息）

