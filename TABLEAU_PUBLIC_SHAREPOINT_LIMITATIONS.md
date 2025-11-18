# Tableau Public 连接 SharePoint 的限制和解决方案

## ⚠️ 重要限制

### Tableau Public 无法直接连接需要认证的 SharePoint

**Tableau Public 的限制：**
- ❌ **不能连接需要认证的数据源**（如需要登录的 SharePoint）
- ❌ **不能使用 OAuth 或用户名/密码认证**
- ✅ 只能连接**公开数据源**（公开的 CSV、Excel、Google Sheets 等）
- ✅ 可以连接 Tableau Public 上的数据源

## 为什么有这个限制？

Tableau Public 是免费服务，为了安全和管理，它：
- 不允许存储用户凭证
- 不允许连接到私有数据源
- 所有数据必须是公开的

## 解决方案

### 方案 A: Tableau Desktop + Tableau Public（推荐 ⭐⭐⭐⭐⭐）

**工作流程：**
```
SharePoint (公司账号，内部可见)
    ↓
Tableau Desktop (个人账号，免费试用/学生版)
    ↓ 连接并提取数据
Tableau Public (个人账号，公开)
    ↓
展示作品
```

**步骤：**
1. **安装 Tableau Desktop**
   - 免费试用 14 天
   - 学生版免费（如果符合条件）
   - 下载：https://www.tableau.com/products/desktop

2. **在 Tableau Desktop 中连接 SharePoint**
   - 使用公司账号认证
   - 创建可视化
   - 数据会提取到本地

3. **发布到 Tableau Public**
   - 点击 "Server" → "Tableau Public" → "Save to Tableau Public"
   - 数据会提取并上传到 Tableau Public（公开）
   - 可以设置自动刷新（Tableau Desktop 可以设置提取刷新计划）

**优点：**
- ✅ 可以连接 SharePoint
- ✅ 数据会提取到 Tableau Public，不需要持续连接
- ✅ 可以设置自动刷新
- ✅ 完全免费（Tableau Desktop 试用 + Tableau Public）

**缺点：**
- ⚠️ 需要 Tableau Desktop（免费试用或学生版）
- ⚠️ 数据会公开（提取到 Tableau Public）

### 方案 B: 导出为公开数据源（简单但需要手动操作）

**工作流程：**
```
SharePoint (公司账号)
    ↓ 定期导出
CSV/Excel (上传到公开位置)
    ↓
Tableau Public (个人账号)
```

**步骤：**
1. **定期从 SharePoint 导出数据**
   - 手动导出或使用脚本自动导出
   - 导出为 CSV 或 Excel

2. **上传到公开位置**
   - GitHub（公开仓库）
   - Google Drive（设置为公开）
   - Dropbox（公开链接）

3. **Tableau Public 连接公开数据源**
   - 直接连接公开的 CSV/Excel 链接

**优点：**
- ✅ 完全免费
- ✅ Tableau Public 可以直接连接
- ✅ 简单直接

**缺点：**
- ⚠️ 需要手动或自动导出
- ⚠️ 数据会公开
- ⚠️ 不是实时数据（需要定期更新）

### 方案 C: 使用 Tableau Online（付费，但功能完整）

**工作流程：**
```
SharePoint (公司账号)
    ↓
Tableau Online (付费订阅)
    ↓
内部人员访问
```

**步骤：**
1. **订阅 Tableau Online**
   - 付费服务（约 $70/用户/月）
   - 支持连接 SharePoint（需要认证）

2. **连接 SharePoint**
   - 在 Tableau Online 中创建数据源
   - 使用公司账号认证
   - 设置权限控制

**优点：**
- ✅ 可以连接 SharePoint
- ✅ 可以控制访问权限（内部人员可见）
- ✅ 实时数据刷新
- ✅ 不需要 Tableau Desktop

**缺点：**
- ❌ 需要付费订阅
- ❌ 不适合个人作品展示

## 推荐方案：Tableau Desktop + Tableau Public

### 为什么推荐这个方案？

1. **完全免费**
   - Tableau Desktop 免费试用 14 天
   - 学生版免费
   - Tableau Public 完全免费

2. **适合展示作品**
   - Tableau Public 可以分享链接
   - 可以嵌入 WordPress
   - 可以展示你的数据分析能力

3. **数据流程清晰**
   - SharePoint 存储原始数据（公司账号）
   - Tableau Desktop 连接并提取（个人账号）
   - Tableau Public 展示（个人账号）

### 实施步骤

1. **安装 Tableau Desktop**
   ```bash
   # 下载并安装 Tableau Desktop
   # 免费试用 14 天，或使用学生版
   ```

2. **连接 SharePoint**
   - 打开 Tableau Desktop
   - 选择 "Microsoft SharePoint Lists"
   - 输入 SharePoint 站点 URL
   - 使用公司账号登录

3. **创建可视化**
   - 设计仪表板
   - 添加交互式筛选器
   - 设置自动刷新（可选）

4. **发布到 Tableau Public**
   - 点击 "Server" → "Tableau Public"
   - 登录 Tableau Public 账户
   - 数据会提取并上传

## 关于个人账号使用

### ✅ 可以使用个人 Tableau Public 账号

- Tableau Public 是免费的
- 可以使用个人账号
- 适合展示作品

### 数据隐私说明

- ⚠️ **Tableau Public 上的数据是公开的**
- ⚠️ 任何人只要有链接都可以查看
- ✅ 适合展示作品，不适合敏感数据

### 展示作品的优势

- ✅ 可以分享链接给任何人
- ✅ 可以嵌入到 WordPress
- ✅ 可以展示你的数据分析能力
- ✅ 可以添加到作品集

## 总结

| 方案 | 成本 | 难度 | 数据隐私 | 推荐度 |
|------|------|------|---------|--------|
| **Tableau Desktop + Public** | 免费 | 中等 | ⚠️ 公开 | ⭐⭐⭐⭐⭐ |
| **导出为公开数据源** | 免费 | 简单 | ⚠️ 公开 | ⭐⭐⭐⭐ |
| **Tableau Online** | 付费 | 简单 | ✅ 私有 | ⭐⭐⭐ |

## 最终推荐

**使用 Tableau Desktop + Tableau Public**：
- ✅ 完全免费
- ✅ 可以连接 SharePoint
- ✅ 适合展示作品
- ✅ 可以设置自动刷新

**工作流程：**
1. GitHub Actions 定时收集 → SharePoint（公司账号）
2. Tableau Desktop 连接 SharePoint → 提取数据
3. 发布到 Tableau Public（个人账号）→ 展示作品

需要我帮你完成代码迁移到 SharePoint 吗？

