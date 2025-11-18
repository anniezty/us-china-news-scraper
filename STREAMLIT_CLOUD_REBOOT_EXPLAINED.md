# Streamlit Cloud "Reboot" 功能说明

## 什么是 "Reboot"？

**Reboot（重启）** 是 Streamlit Cloud 的一个功能，用于重新启动你的应用。

### 作用
- **重新加载配置**：应用会重新读取 Streamlit Secrets 中的最新配置
- **清除缓存**：清除应用的内存缓存和临时数据
- **应用更新**：如果代码有更新，会重新部署最新版本
- **解决临时问题**：有时应用出现异常，重启可以恢复正常

## 什么时候需要 Reboot？

### 1. 更新 Secrets 后（最常见）
当你更新了 Streamlit Cloud Secrets（例如修改了 API key、密码、截止日期等），需要重启应用才能让新配置生效。

### 2. 应用出现异常
如果应用出现错误、卡住或行为异常，重启通常可以解决问题。

### 3. 代码更新后未自动部署
虽然 Streamlit Cloud 通常会自动检测 GitHub 更新并重新部署，但有时需要手动触发。

## 如何找到 Reboot 功能？

### 方法 1: 应用设置页面
1. 登录 Streamlit Cloud: https://share.streamlit.io/
2. 进入你的应用
3. 点击右上角的 **"⋮"**（三个点）菜单
4. 选择 **"Settings"** 或 **"Manage app"** → **"Settings"**
5. 在设置页面，找到 **"Reboot app"** 或 **"Restart app"** 按钮
6. 点击按钮，等待重启完成（通常 30 秒到 2 分钟）

### 方法 2: 应用列表
1. 在 Streamlit Cloud 应用列表中
2. 找到你的应用
3. 点击应用旁边的 **"⋮"**（三个点）菜单
4. 选择 **"Reboot"** 或 **"Restart"**

### 方法 3: 应用详情页
1. 点击应用名称进入应用详情页
2. 在页面顶部或侧边栏，查找 **"Reboot"** 或 **"Restart"** 按钮

## Reboot vs. 其他操作

| 操作 | 作用 | 使用场景 |
|------|------|---------|
| **Reboot/Restart** | 重启应用，重新加载配置 | 更新 Secrets 后 |
| **Redeploy** | 重新部署应用（从 GitHub） | 代码更新后 |
| **Delete** | 删除应用 | 不再需要应用时 |

## 注意事项

1. **Reboot 不会丢失数据**
   - 不会影响 Google Sheets 中的数据
   - 不会影响已保存的配置
   - 只会清除应用的内存状态

2. **Reboot 需要时间**
   - 通常需要 30 秒到 2 分钟
   - 重启期间应用可能暂时无法访问

3. **Reboot 后需要刷新页面**
   - 重启完成后，刷新浏览器页面
   - 使用 `Ctrl+Shift+R`（Windows）或 `Cmd+Shift+R`（Mac）强制刷新

## 常见问题

### Q: Reboot 后配置还是不生效？
A: 
1. 确认 Secrets 已正确保存
2. 等待 1-2 分钟让 Secrets 传播
3. 再次 Reboot
4. 强制刷新浏览器页面

### Q: 找不到 Reboot 按钮？
A: 
- 某些 Streamlit Cloud 版本可能使用不同的术语（"Restart"、"Redeploy"）
- 或者可以通过 GitHub 提交来触发自动重新部署

### Q: Reboot 会影响正在使用的用户吗？
A: 
- 是的，重启期间应用会暂时无法访问
- 通常只需要 30 秒到 2 分钟
- 建议在非高峰时段进行重启

## 总结

**Reboot = 重启应用 = 让新配置生效**

当你更新了 Streamlit Cloud Secrets 后，记得点击 **"Reboot app"** 按钮，这样应用才会读取最新的配置。

