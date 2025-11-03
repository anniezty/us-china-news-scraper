# API 密钥安全指南

## ⚠️ 重要：永远不要将 API key 提交到 GitHub！

API key 是敏感信息，必须安全保存。

## ✅ 正确的做法

### 方法 1: 使用环境变量（本地开发）

**创建 `.env` 文件**（已经在 `.gitignore` 中，不会被提交）：

```bash
# .env 文件
API_CLASSIFIER_ENABLED=true
API_PROVIDER=openai
OPENAI_API_KEY=sk-your-actual-key-here
OPENAI_MODEL=gpt-4o-mini
```

**加载环境变量**：
```bash
# 使用 python-dotenv（可选）
pip install python-dotenv

# 或者在代码中直接使用
export OPENAI_API_KEY=sk-your-key
```

### 方法 2: Streamlit Cloud Secrets（生产环境推荐）

在 Streamlit Cloud 部署时，使用 Secrets 功能：

1. **访问 Streamlit Cloud**
   - 打开你的应用
   - 点击 Settings → Secrets

2. **添加 Secrets**
   ```toml
   [api]
   classifier_enabled = true
   provider = "openai"
   openai_api_key = "sk-your-actual-key-here"
   openai_model = "gpt-4o-mini"
   ```

3. **代码会自动读取**
   - `api_classifier.py` 会自动从 `st.secrets` 读取
   - 无需修改代码

### 方法 3: 系统环境变量（服务器部署）

```bash
export OPENAI_API_KEY=sk-your-key
export API_CLASSIFIER_ENABLED=true
```

## ❌ 错误做法（不要这样做）

```python
# ❌ 永远不要硬编码 API key
api_key = "sk-abc123..."  # 危险！

# ❌ 不要提交到代码仓库
# 即使注释掉也不安全
# api_key = "sk-abc123..."
```

## 📋 检查清单

部署前检查：

- [ ] `.env` 文件在 `.gitignore` 中 ✅（已配置）
- [ ] 没有在代码中硬编码 API key ✅（已确认）
- [ ] Streamlit Cloud 使用 Secrets ✅（推荐）
- [ ] 本地使用环境变量 ✅（推荐）

## 🔍 如何验证

**检查是否意外提交了 API key**：

```bash
# 在 Git 历史中搜索（如果担心）
git log -p | grep -i "sk-"
git log -p | grep -i "api.*key"

# 检查当前文件
grep -r "sk-" . --exclude-dir=.git --exclude-dir=__pycache__
```

## 🛡️ 安全最佳实践

1. **使用不同的 API key**
   - 开发环境一个 key
   - 生产环境另一个 key
   - 如果泄露可以单独撤销

2. **限制 API key 权限**
   - 只给必要的权限
   - 设置使用限制（如每月限额）

3. **定期轮换**
   - 定期更换 API key
   - 如果怀疑泄露，立即更换

4. **监控使用**
   - 定期检查 API 使用情况
   - 发现异常立即处理

## 📝 总结

✅ **API key 通过环境变量或 Secrets 传递**
✅ **`.env` 文件在 `.gitignore` 中，不会提交**
✅ **代码中没有任何硬编码的 key**
✅ **Streamlit Cloud 使用 Secrets 功能**

**你的 API key 是安全的！** 🔒

