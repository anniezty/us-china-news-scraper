# GitHub 认证设置

## 问题

GitHub 不再支持密码认证，需要使用 **Personal Access Token**。

## 解决步骤

### 第一步：创建 Personal Access Token

1. **打开浏览器**，访问：https://github.com/settings/tokens
2. **点击 "Generate new token"** → **"Generate new token (classic)"**
3. **填写信息**：
   - Note: `us-china-picker` (描述用途)
   - Expiration: 选择期限（建议 90 天或 No expiration）
   - **勾选权限**：
     - ✅ `repo` (全部权限)
4. **点击 "Generate token"**
5. **复制 token**（只显示一次，务必保存！）
   - 格式类似：`ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### 第二步：使用 Token 推送代码

在 Terminal 中执行：

```bash
# 推送代码（会提示输入用户名和密码）
git push -u origin main
```

**当提示输入时**：
- Username: `anniezty`
- Password: **粘贴刚才复制的 token**（不是你的 GitHub 密码）

### 或者：使用 Token 直接配置（更简单）

```bash
# 将 token 直接添加到 URL（替换 YOUR_TOKEN 为实际 token）
git remote set-url origin https://YOUR_TOKEN@github.com/anniezty/us-china-news-scrapper.git

# 然后推送
git push -u origin main
```

### 第三步：验证推送成功

推送成功后，访问：
https://github.com/anniezty/us-china-news-scrapper

应该能看到所有代码文件。

## 注意事项

⚠️ **Token 安全**：
- 不要将 token 提交到代码仓库
- 不要分享 token 给他人
- Token 泄露后立即在 GitHub 设置中删除

## 完成后

推送成功后，继续下一步：部署到 Streamlit Cloud！

