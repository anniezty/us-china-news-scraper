# Streamlit Cloud API 配置故障排除指南

## 问题：勾选了 API 分类，但没有启动 API

### 可能的原因

1. **Streamlit Cloud Secrets 配置不正确**
   - `classifier_enabled` 未设置为 `true`
   - API key 未正确配置
   - Secrets 格式错误

2. **Secrets 未正确保存或应用**
   - 保存后未重新部署
   - Secrets 格式不符合 TOML 规范

3. **API key 格式问题**
   - API key 不完整或无效
   - 使用了错误的 key（例如使用了本地环境的 key）

## 诊断步骤

### 1. 检查 Streamlit Cloud Secrets 配置

1. 登录 Streamlit Cloud: https://share.streamlit.io/
2. 进入你的应用 → **Settings** → **Secrets**
3. 确认以下配置存在且正确：

```toml
[api]
classifier_enabled = true
provider = "openai"
openai_api_key = "sk-proj-..."
openai_model = "gpt-4o-mini"
daily_budget_usd = 1.0
cost_per_call_usd = 0.001
```

**重要提示**：
- `classifier_enabled` 必须是 `true`（布尔值）或 `"true"`（字符串）
- `openai_api_key` 必须以 `sk-` 开头
- 确保没有多余的空格或引号

### 2. 检查应用中的调试信息

当你在 Streamlit Cloud 上勾选 "🤖 Use API Classification (OpenAI)" 时：

1. **如果 API 可用**：
   - 会显示 "💰 API Budget Status: $X.XXX used today ($X.XXX remaining)"
   - 分类时会显示 "✅ Using API classification (95-98% accuracy)"

2. **如果 API 不可用**：
   - 会显示 "🔍 API Configuration Debug Info" 展开框
   - 显示详细的配置状态（`classifier_enabled`、`openai_api_key` 等）

### 3. 检查 Streamlit Cloud 日志

1. 进入应用 → **Settings** → **Logs**
2. 查看 `stderr` 日志，查找以下调试信息：
   - `🔍 assign_category() called with use_api_classification=True`
   - `🔍 is_api_available() check in assign_category: True/False`
   - `🔍 Debug: classifier_enabled = ...`
   - `🔍 Debug: openai_api_key exists = ...`

### 4. 常见错误和解决方案

#### 错误 1: `classifier_enabled` 未找到或为 false

**症状**：
- 调试信息显示：`❌ classifier_enabled not found in secrets` 或 `❌ classifier_enabled is false`

**解决方案**：
```toml
[api]
classifier_enabled = true  # 确保是 true（不是 "true" 字符串，除非代码支持）
```

#### 错误 2: `openai_api_key` 未找到或无效

**症状**：
- 调试信息显示：`❌ openai_api_key is empty or not found` 或 `❌ openai_api_key seems invalid (too short)`

**解决方案**：
1. 确认 API key 已正确复制（包括 `sk-proj-` 前缀）
2. 确认 API key 在 OpenAI 门户中仍然有效
3. 检查是否有多余的空格或换行符

#### 错误 3: Secrets 格式错误

**症状**：
- 应用无法读取 secrets
- 调试信息显示：`❌ No [api] section found in Streamlit secrets`

**解决方案**：
1. 确保使用正确的 TOML 格式
2. 确保 `[api]` 部分在 secrets 文件中
3. 检查是否有语法错误（缺少引号、括号等）

### 5. 验证配置的步骤

1. **保存 Secrets**：
   - 在 Streamlit Cloud Secrets 中保存配置
   - 等待应用自动重新部署（或手动触发重新部署）

2. **测试 API 可用性**：
   - 勾选 "🤖 Use API Classification (OpenAI)"
   - 查看是否显示预算状态（表示 API 可用）
   - 如果显示错误，查看调试信息

3. **运行分类测试**：
   - 选择少量文章（例如 5-10 篇）
   - 点击 "Generate & Export"
   - 查看是否显示 "✅ Using API classification"
   - 检查日志中的 API 调用记录

### 6. 手动测试 API 配置

如果问题仍然存在，可以在 Streamlit Cloud 的 Python 控制台中测试：

```python
import streamlit as st

# 检查 secrets
if hasattr(st, "secrets") and "api" in st.secrets:
    api_config = st.secrets.get("api", {})
    print(f"classifier_enabled: {api_config.get('classifier_enabled')}")
    print(f"openai_api_key exists: {bool(api_config.get('openai_api_key'))}")
    print(f"openai_api_key length: {len(api_config.get('openai_api_key', ''))}")
else:
    print("No [api] section in secrets")
```

### 7. 联系支持

如果以上步骤都无法解决问题，请提供以下信息：

1. Streamlit Cloud 日志（特别是 `stderr` 部分）
2. Secrets 配置（**隐藏 API key**）
3. 调试信息截图
4. 应用 URL

## 预防措施

1. **使用模板文件**：
   - 使用 `streamlit_secrets_for_cloud.toml` 作为模板
   - 确保格式正确后再复制到 Streamlit Cloud

2. **测试本地配置**：
   - 先在本地 `.streamlit/secrets.toml` 中测试
   - 确认无误后再部署到 Streamlit Cloud

3. **定期检查 API key**：
   - 确认 API key 在 OpenAI 门户中仍然有效
   - 检查是否有使用限制或配额问题
