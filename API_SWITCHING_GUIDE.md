# API Key 切换指南

## 📋 概述

本指南说明如何从个人 API key 切换到公司 API key，确保切换流畅且不丢失数据。

## ✅ 数据安全保证

### 不会丢失的数据

1. **分类结果**: 存储在 Google Sheets 中，与 API key 无关
2. **历史文章**: 在 Google Sheets 中，永久保存
3. **分类规则**: 在 `categories_en.yaml` 中，不会丢失
4. **已分类的数据**: 切换 API key 不会影响已分类的文章

### 重要说明

- **API key 只用于分类新文章**
- **已分类的文章结果不会改变**
- **切换 API key 后，新文章会使用新的 API key 分类**
- **历史数据完全安全**

## 🔄 切换流程

### 场景 1: 本地开发环境（个人 → 公司）

**当前状态**: 使用个人 API key 测试

**切换到公司 API key**:

1. 编辑 `.streamlit/secrets.toml`
2. 修改：
   ```toml
   [api]
   classifier_enabled = true
   provider = "openai"
   openai_api_key = "sk-公司-API-key"  # 改为公司 key
   ```
3. 保存文件
4. 重启 Streamlit 应用

**验证**:
- 运行一次分类，确认使用新的 API key
- 检查分类结果是否正常

### 场景 2: Streamlit Cloud（个人 → 公司）

**当前状态**: 使用个人 API key

**切换到公司 API key**:

1. 登录 Streamlit Cloud
2. 进入应用的 Settings → Secrets
3. 添加或更新 `[api]` 部分：
   ```toml
   [api]
   classifier_enabled = true
   provider = "openai"
   openai_api_key = "sk-公司-API-key"
   ```
4. 保存并重新部署应用

**验证**:
- 访问应用，运行一次分类
- 确认使用新的 API key

### 场景 3: 定时任务（cron/launchd）

**当前状态**: 使用个人 API key

**切换到公司 API key**:

**方式 A: 修改 launchd plist 文件**

编辑 `~/Library/LaunchAgents/com.uschina.dailycollector.plist`，添加：
```xml
<key>EnvironmentVariables</key>
<dict>
    <key>PATH</key>
    <string>/Users/tingyuzheng/.pyenv/versions/3.11.9/bin:/usr/local/bin:/usr/bin:/bin</string>
    <key>OPENAI_API_KEY</key>
    <string>sk-公司-API-key</string>
    <key>API_CLASSIFIER_ENABLED</key>
    <string>true</string>
</dict>
```

然后重新加载：
```bash
launchctl unload ~/Library/LaunchAgents/com.uschina.dailycollector.plist
launchctl load ~/Library/LaunchAgents/com.uschina.dailycollector.plist
```

**方式 B: 使用环境变量文件**

创建 `~/.us_china_env` 文件：
```bash
export OPENAI_API_KEY="sk-公司-API-key"
export API_CLASSIFIER_ENABLED="true"
```

在 plist 中引用：
```xml
<key>EnvironmentVariables</key>
<dict>
    <key>PATH</key>
    <string>/Users/tingyuzheng/.pyenv/versions/3.11.9/bin:/usr/local/bin:/usr/bin:/bin</string>
</dict>
<key>ProgramArguments</key>
<array>
    <string>/bin/bash</string>
    <string>-c</string>
    <string>source ~/.us_china_env && /Users/tingyuzheng/.pyenv/versions/3.11.9/bin/python3 /Users/tingyuzheng/Downloads/us_china_picker/daily_collector_to_sheets.py</string>
</array>
```

## 🔐 多环境配置策略

### 推荐方案

1. **本地开发**: 使用 `.streamlit/secrets.toml`（个人 API key）
2. **Streamlit Cloud**: 使用 Streamlit Cloud Secrets（公司 API key）
3. **定时任务**: 使用环境变量（公司 API key）

### 配置优先级

1. Streamlit Secrets（最高优先级）
2. 环境变量
3. 默认值（关键字分类）

## 📝 配置备份

### 备份个人配置

在切换前，备份当前的配置：

```bash
# 备份个人配置（不包含真实 key）
cp .streamlit/secrets.toml .streamlit/secrets.toml.personal.backup
```

### 创建配置模板

使用 `.streamlit/secrets.toml.example` 作为模板，不包含真实 key，可以安全提交到 GitHub。

## 🧪 测试切换

### 切换前测试

1. 确认当前 API key 工作正常
2. 记录当前分类结果（作为基准）

### 切换后测试

1. 运行一次分类
2. 验证新 API key 工作正常
3. 检查分类结果是否合理
4. 确认历史数据未受影响

## 💡 最佳实践

1. **分离配置**: 个人和公司 API key 分开管理
2. **版本控制**: 配置模板提交到 Git，真实 key 不提交
3. **文档记录**: 记录使用的 API key 来源（个人/公司）
4. **定期检查**: 确认 API key 有效且未过期

## ⚠️ 注意事项

1. **不要提交真实 API key 到 GitHub**
2. **定期轮换 API key**（安全最佳实践）
3. **监控 API 使用量**（避免意外费用）
4. **备份重要配置**（切换前）

## 📊 数据迁移检查清单

切换 API key 后，确认：

- [ ] 新 API key 工作正常
- [ ] 分类结果合理
- [ ] 历史数据未受影响
- [ ] Google Sheets 数据完整
- [ ] 定时任务正常运行（如果使用）
- [ ] Streamlit Cloud 正常运行（如果使用）

## 🔄 回滚方案

如果需要回滚到个人 API key：

1. 恢复 `.streamlit/secrets.toml` 中的个人 API key
2. 或恢复备份的配置文件
3. 重启应用
4. 验证工作正常

**注意**: 回滚不会影响已分类的数据，只是新文章会使用旧的 API key 分类。

