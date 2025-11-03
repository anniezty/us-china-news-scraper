# API 分类使用指南

## 概述

系统支持使用 AI API（OpenAI 或 Anthropic）进行更精准的文章分类。当前默认使用正则表达式分类，API 分类是可选的，需要时启用。

## 为什么需要 API 分类？

- **更精准**: AI 理解语义，能识别更复杂的分类场景
- **更灵活**: 不需要维护复杂的正则表达式
- **更智能**: 能理解上下文和隐含含义

## 启用方式

### ⚠️ 重要：API Key 安全

**永远不要将 API key 提交到 GitHub！** 使用环境变量或 Streamlit Secrets。

### 方法 1: 本地开发 - 使用 .env 文件（推荐）

**创建 `.env` 文件**（已在 `.gitignore` 中，不会被提交）：

```bash
# .env 文件（不要提交到 Git！）
API_CLASSIFIER_ENABLED=true
API_PROVIDER=openai
OPENAI_API_KEY=sk-your-actual-key-here
OPENAI_MODEL=gpt-4o-mini
```

**加载环境变量**：
```bash
# 方式 1: 直接 export（Linux/macOS）
export OPENAI_API_KEY=sk-your-key
export API_CLASSIFIER_ENABLED=true

# 方式 2: 使用 python-dotenv
pip install python-dotenv
# 代码中会自动加载 .env 文件
```

### 方法 2: Streamlit Cloud Secrets（生产环境推荐）

在 Streamlit Cloud 的 Settings → Secrets 中添加：

```toml
[api]
classifier_enabled = true
provider = "openai"
openai_api_key = "sk-your-actual-key-here"
openai_model = "gpt-4o-mini"
```

**优点**：
- ✅ 安全，不会泄露
- ✅ 自动读取，无需修改代码
- ✅ 可以随时更新，无需重新部署

## 支持的 API 提供商

### OpenAI

**优点**:
- 模型选择多（GPT-4, GPT-3.5, GPT-4o-mini）
- 速度快
- 价格相对便宜（GPT-4o-mini）

**设置**:
```bash
export API_PROVIDER=openai
export OPENAI_API_KEY=sk-...
export OPENAI_MODEL=gpt-4o-mini  # 或 gpt-4, gpt-3.5-turbo
```

**安装依赖**:
```bash
pip install openai
```

### Anthropic (Claude)

**优点**:
- 理解能力强
- 输出质量高

**设置**:
```bash
export API_PROVIDER=anthropic
export ANTHROPIC_API_KEY=sk-ant-...
export ANTHROPIC_MODEL=claude-3-haiku-20240307  # 或 claude-3-opus
```

**安装依赖**:
```bash
pip install anthropic
```

## 成本估算

### OpenAI GPT-4o-mini
- **输入**: ~$0.15 / 1M tokens
- **输出**: ~$0.60 / 1M tokens
- **每篇文章**: ~500 tokens (标题+摘要)
- **成本**: 约 $0.0003 / 篇文章
- **1000 篇文章**: ~$0.30

### Anthropic Claude Haiku
- **输入**: ~$0.25 / 1M tokens
- **输出**: ~$1.25 / 1M tokens
- **每篇文章**: ~500 tokens
- **成本**: 约 $0.0005 / 篇文章
- **1000 篇文章**: ~$0.50

## 工作流程

1. **默认（正则）**: 使用正则表达式快速分类
2. **启用 API 后**: 
   - 先尝试 API 分类
   - 如果 API 失败或未启用，回退到正则分类
   - 确保始终有分类结果

## 最佳实践

### 混合使用

**推荐策略**:
- 大部分文章用正则（快速、免费）
- 复杂/不确定的文章用 API（精准）

**实现方式**:
```python
# 先尝试正则
for cat, rgx in compiled:
    if rgx.search(text):
        return cat

# 如果正则未匹配，使用 API
if not matched:
    api_cat = classify_with_api(headline, nut_graph, categories)
    if api_cat:
        return api_cat
```

### 缓存结果

可以缓存 API 分类结果，避免重复调用：
- 使用文章 URL 作为 key
- 存储分类结果
- 相同文章不再调用 API

## 注意事项

1. **API 成本**: 大量文章会产生 API 费用
2. **速度**: API 调用比正则慢（需要网络请求）
3. **依赖**: 需要网络连接和 API key
4. **回退**: 代码会自动回退到正则，确保可用性

## 未来扩展

如果需要更高级的功能：
- 批量分类优化
- 结果缓存
- 自定义提示词
- 多模型对比

## 总结

✅ **可选功能**: 不需要时完全不影响现有功能
✅ **易于启用**: 设置环境变量即可
✅ **自动回退**: API 不可用时自动使用正则
✅ **成本可控**: 可以选择便宜的模型或混合使用

**建议**: 先用正则分类，如果发现准确率不够，再启用 API 分类。

