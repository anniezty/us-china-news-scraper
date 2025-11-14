# API 分类器配置指南

## 📋 配置方式

### 方式 1: Streamlit Secrets（推荐 - 本地和云端）

编辑 `.streamlit/secrets.toml`：

```toml
[api]
classifier_enabled = true
provider = "openai"  # 或 "anthropic"
openai_api_key = "sk-你的-API-key"
# openai_model = "gpt-4o-mini"  # 可选
```

### 方式 2: 环境变量（适合脚本和定时任务）

```bash
export OPENAI_API_KEY="sk-你的-API-key"
export API_CLASSIFIER_ENABLED="true"
export API_PROVIDER="openai"  # 可选
```

## 🔄 切换 API 账号

### 从个人账号切换到公司账号

**步骤 1: 更新配置**

编辑 `.streamlit/secrets.toml`，修改：
```toml
openai_api_key = "sk-公司-API-key"
```

**步骤 2: 重启应用**

- 本地：重启 Streamlit 应用
- 云端：重新部署或重启 Streamlit Cloud

**步骤 3: 验证**

运行一次分类，确认使用新的 API key。

## 📊 数据安全

### ✅ 不会丢失的数据

1. **分类结果**: 存储在 Google Sheets 中，不会丢失
2. **历史文章**: 在 Google Sheets 中，不会丢失
3. **分类规则**: 在 `categories_en.yaml` 中，不会丢失

### ⚠️ 注意事项

- API key 切换不会影响已分类的数据
- 分类结果存储在 Google Sheets 中，与 API key 无关
- 切换 API key 后，新文章会使用新的 API key 分类

## 🔐 多环境配置

### 本地开发环境

使用 `.streamlit/secrets.toml`（个人 API key）

### 生产环境（Streamlit Cloud）

在 Streamlit Cloud 的 Secrets 中配置公司 API key

### 定时任务（cron/launchd）

使用环境变量：
```bash
export OPENAI_API_KEY="sk-公司-API-key"
export API_CLASSIFIER_ENABLED="true"
```

## 📝 配置优先级

1. Streamlit Secrets（最高优先级）
2. 环境变量
3. 默认值（如果都未设置，使用关键字分类）

## 💡 最佳实践

1. **个人测试**: 使用 `.streamlit/secrets.toml`（本地）
2. **公司生产**: 使用 Streamlit Cloud Secrets（云端）
3. **定时任务**: 使用环境变量（cron/launchd）
4. **备份配置**: 保存配置模板（不包含真实 key）

