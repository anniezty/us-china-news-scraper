# 🔒 云端部署安全指南

## ✅ 敏感信息保护状态

所有敏感信息都已通过 `.gitignore` 保护，**不会**被上传到 GitHub：

### 已保护的敏感文件：
- ✅ `.streamlit/secrets.toml` - 本地 API key 和配置
- ✅ `streamlit_secrets_for_cloud.toml` - 云端配置模板（含 Google credentials）
- ✅ `google_credentials.json` - Google 服务账号密钥
- ✅ `.secrets/` 目录 - 包含所有 cookie 文件
- ✅ `wapo_cookie.txt`, `axios_cookie.txt`, `bloomberg_cookie.txt` - Cookie 文件
- ✅ `.env`, `.env.local` - 环境变量文件
- ✅ 所有 `*_api_key.txt`, `*_secret.txt` 文件

### 可以安全同步的文件：
- ✅ 所有 Python 代码文件（`.py`）
- ✅ 配置文件（`config_en.yaml`, `categories_en.yaml`）
- ✅ `requirements.txt`
- ✅ 文档文件（`.md`）
- ✅ 脚本文件（`scripts/*.sh`）

---

## 📋 Streamlit Cloud 部署步骤

### 1. 推送代码到 GitHub
```bash
git add .
git commit -m "Ready for cloud deployment"
git push origin main
```

### 2. 在 Streamlit Cloud 中配置 Secrets

1. **登录 Streamlit Cloud**：https://share.streamlit.io/
2. **连接 GitHub 仓库**
3. **进入 "Secrets" 配置页面**
4. **复制 `streamlit_secrets_for_cloud.toml` 的内容**（本地文件，不会上传）
5. **粘贴到 Streamlit Cloud 的 Secrets 编辑器**

### 3. 在 Secrets 中配置的内容

```toml
GOOGLE_SHEETS_ID = "your-sheets-id"

[google_sheets]
credentials = '''
{
  "type": "service_account",
  "project_id": "...",
  "private_key": "...",
  ...
}
'''

[api]
classifier_enabled = true
provider = "openai"
openai_api_key = "sk-your-api-key"
openai_model = "gpt-4o-mini"
daily_budget_usd = 1.0
cost_per_call_usd = 0.001

[test_mode]
enabled = false
password = ""
deadline = ""
```

### 4. 部署应用

- Streamlit Cloud 会自动检测 `app_with_sheets_db.py` 作为主应用
- 部署完成后，应用会在云端运行

---

## 🔐 安全最佳实践

### ✅ 已实施的安全措施：

1. **`.gitignore` 保护**
   - 所有敏感文件都在 `.gitignore` 中
   - 确保不会意外提交敏感信息

2. **环境变量分离**
   - 本地使用 `.streamlit/secrets.toml`
   - 云端使用 Streamlit Cloud Secrets
   - 两者完全分离，互不影响

3. **API 预算控制**
   - 每日预算限制（`daily_budget_usd`）
   - 每次调用成本跟踪（`cost_per_call_usd`）
   - 自动停止超过预算的调用

4. **访问控制**
   - 测试模式密码保护
   - 时间限制（deadline）
   - 可以随时禁用测试访问

### ⚠️ 注意事项：

1. **不要**在代码中硬编码 API key 或 credentials
2. **不要**将 `secrets.toml` 或 `streamlit_secrets_for_cloud.toml` 推送到 GitHub
3. **不要**在公开的 GitHub Issues 或 PR 中分享敏感信息
4. **定期**检查 GitHub 仓库，确保没有敏感信息泄露

---

## 🔍 安全检查清单

在推送代码到 GitHub 之前，请确认：

- [ ] `.streamlit/secrets.toml` 在 `.gitignore` 中 ✅
- [ ] `streamlit_secrets_for_cloud.toml` 在 `.gitignore` 中 ✅
- [ ] `google_credentials.json` 在 `.gitignore` 中 ✅
- [ ] `.secrets/` 目录在 `.gitignore` 中 ✅
- [ ] 所有 cookie 文件在 `.gitignore` 中 ✅
- [ ] 代码中没有硬编码的 API key ✅
- [ ] 代码中没有硬编码的 credentials ✅

---

## 📞 如果发现敏感信息泄露

如果发现敏感信息被意外提交到 GitHub：

1. **立即**在相关服务中撤销/重新生成 API key 或 credentials
2. **使用** `git filter-branch` 或 `git filter-repo` 从历史记录中删除敏感文件
3. **强制推送**清理后的历史记录（⚠️ 需要团队协作）
4. **考虑**使用 GitHub 的 Secret Scanning 功能

---

## ✅ 总结

✅ **所有敏感信息都已保护，可以安全同步到 GitHub**  
✅ **云端部署时需要在 Streamlit Cloud 的 Secrets 中手动配置**  
✅ **不会泄漏 API key、Google credentials、cookie 等敏感信息**

