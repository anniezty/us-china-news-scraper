# Tableau 嵌入 WordPress 指南

## ✅ 是的，Tableau 可以嵌入到 WordPress

有几种方法可以将 Tableau 可视化嵌入到 WordPress 网站中。

## 方法 1: Tableau Public（免费，最简单）

### 步骤：
1. **发布到 Tableau Public**
   - 在 Tableau Desktop 中创建可视化
   - 发布到 Tableau Public（免费账户）
   - 获取嵌入代码

2. **在 WordPress 中嵌入**
   - 使用 HTML 块或自定义 HTML 小工具
   - 粘贴 Tableau 提供的嵌入代码（iframe）

### 优点：
- ✅ 免费
- ✅ 简单易用
- ✅ 不需要服务器

### 缺点：
- ⚠️ 数据是公开的（Tableau Public）
- ⚠️ 需要手动更新数据

## 方法 2: Tableau Server/Online（付费，更强大）

### 步骤：
1. **发布到 Tableau Server 或 Tableau Online**
   - 在 Tableau Desktop 中创建可视化
   - 发布到 Tableau Server/Online
   - 获取嵌入 URL 和访问令牌

2. **在 WordPress 中嵌入**
   - 使用 iframe 或 Tableau JavaScript API
   - 配置身份验证（如果需要）

### 优点：
- ✅ 数据可以私有
- ✅ 支持实时数据刷新
- ✅ 更强大的功能

### 缺点：
- ❌ 需要付费订阅（Tableau Server/Online）
- ⚠️ 需要配置身份验证

## 方法 3: Tableau JavaScript API（高级）

### 步骤：
1. **使用 Tableau JavaScript API**
   - 在 WordPress 中加载 Tableau JavaScript 库
   - 使用 API 创建交互式嵌入

### 优点：
- ✅ 完全自定义
- ✅ 更好的集成体验

### 缺点：
- ⚠️ 需要编程知识
- ⚠️ 需要 Tableau Server/Online

## 替代方案：直接使用 Streamlit

### 为什么不使用 Tableau？

对于你的项目（US-China News Scraper），**直接嵌入 Streamlit 应用可能更简单**：

### 方法 A: Streamlit Cloud 嵌入

1. **部署到 Streamlit Cloud**（你已经做了）
2. **在 WordPress 中嵌入**
   ```html
   <iframe 
     src="https://your-app.streamlit.app" 
     width="100%" 
     height="800" 
     frameborder="0">
   </iframe>
   ```

### 优点：
- ✅ 免费（Streamlit Cloud 免费版）
- ✅ 实时数据（直接从 Google Sheets 读取）
- ✅ 交互式界面（用户可以直接筛选、导出）
- ✅ 不需要额外工具

### 缺点：
- ⚠️ 需要 Streamlit Cloud 账户
- ⚠️ 可能需要处理 iframe 限制

## 方法 B: 导出数据到 WordPress

### 步骤：
1. **定期导出数据**
   - 从 Google Sheets 导出 CSV/JSON
   - 上传到 WordPress 媒体库

2. **使用 WordPress 插件**
   - 使用数据可视化插件（如 Data Tables, Chart.js）
   - 在 WordPress 中直接显示数据

### 优点：
- ✅ 完全控制
- ✅ 不需要外部服务

### 缺点：
- ⚠️ 需要手动更新数据
- ⚠️ 功能有限

## 推荐方案对比

| 方案 | 成本 | 难度 | 实时性 | 推荐度 |
|------|------|------|--------|--------|
| **Streamlit 嵌入** | 免费 | 简单 | ✅ 实时 | ⭐⭐⭐⭐⭐ |
| **Tableau Public** | 免费 | 简单 | ⚠️ 手动更新 | ⭐⭐⭐ |
| **Tableau Server** | 付费 | 中等 | ✅ 实时 | ⭐⭐⭐⭐ |
| **WordPress 插件** | 免费/付费 | 中等 | ⚠️ 手动更新 | ⭐⭐⭐ |

## 具体实施建议

### 对于你的项目，我推荐：

**方案 1: 直接嵌入 Streamlit（最简单）**
```html
<iframe 
  src="https://your-app.streamlit.app" 
  width="100%" 
  height="800" 
  frameborder="0"
  scrolling="auto">
</iframe>
```

**方案 2: 如果 WordPress 不支持 iframe，使用 Tableau Public**
1. 定期从 Google Sheets 导出数据
2. 在 Tableau Desktop 中创建可视化
3. 发布到 Tableau Public
4. 嵌入到 WordPress

## 注意事项

1. **iframe 限制**
   - 某些 WordPress 主题可能限制 iframe
   - 某些浏览器可能阻止 iframe（X-Frame-Options）

2. **性能考虑**
   - Streamlit 应用加载可能需要几秒钟
   - 考虑添加加载提示

3. **移动端适配**
   - 确保 iframe 在移动设备上正常显示
   - 考虑响应式设计

## 总结

- **Tableau 可以嵌入 WordPress**，但需要 Tableau Server/Online 或 Tableau Public
- **对于你的项目，直接嵌入 Streamlit 可能更简单、更实用**
- Streamlit 已经提供了交互式界面，用户可以直接筛选、导出数据

需要我帮你设置 Streamlit 嵌入 WordPress 的具体步骤吗？

