# SharePoint 迁移指南

## 概述

本指南说明如何将项目从 Google Sheets 迁移到 SharePoint，并使用 Tableau Public 连接数据。

## 架构设计

```
GitHub Actions (定时任务)
    ↓
收集新闻文章
    ↓
上传到 SharePoint List (公司账号)
    ↓
Tableau Public (个人账号) 连接 SharePoint
    ↓
展示和交互
```

## 重要说明：Tableau Public 的限制

### ⚠️ Tableau Public 无法直接连接需要认证的 SharePoint

**Tableau Public 的限制：**
- ❌ 不能连接需要认证的数据源（如需要登录的 SharePoint）
- ✅ 只能连接公开数据源（公开的 CSV、Excel、Google Sheets 等）
- ✅ 可以连接 Tableau Public 上的数据源

### 解决方案

#### 方案 A: 使用 Tableau Desktop + Tableau Public（推荐）

**工作流程：**
1. **Tableau Desktop**（个人账号，免费试用 14 天，学生免费）
   - 连接 SharePoint（使用公司账号认证）
   - 创建可视化
   - 发布到 Tableau Public（数据会提取并公开）

**优点：**
- ✅ 可以连接 SharePoint
- ✅ 数据会提取到 Tableau Public，不需要持续连接
- ✅ 可以设置自动刷新（Tableau Desktop 可以设置提取刷新）

**缺点：**
- ⚠️ 需要 Tableau Desktop（免费试用或学生版）
- ⚠️ 数据会公开（提取到 Tableau Public）

#### 方案 B: 导出为公开数据源

**工作流程：**
1. 定期从 SharePoint 导出数据为 CSV/Excel
2. 上传到公开位置（GitHub、Google Drive 公开链接等）
3. Tableau Public 连接公开数据源

**优点：**
- ✅ 完全免费
- ✅ Tableau Public 可以直接连接

**缺点：**
- ⚠️ 需要手动或自动导出
- ⚠️ 数据会公开

#### 方案 C: 使用 Tableau Online（付费）

**工作流程：**
1. 使用 Tableau Online（付费订阅）
2. 连接 SharePoint（支持认证）
3. 设置权限控制（内部人员可见）

**优点：**
- ✅ 可以连接 SharePoint
- ✅ 可以控制访问权限
- ✅ 实时数据刷新

**缺点：**
- ❌ 需要付费订阅

## 推荐方案：Tableau Desktop + Tableau Public

### 步骤 1: 安装 Tableau Desktop

1. **下载 Tableau Desktop**
   - 访问 https://www.tableau.com/products/desktop
   - 下载免费试用版（14 天）
   - 或使用学生版（如果符合条件）

2. **创建 Tableau Public 账户**
   - 访问 https://public.tableau.com/
   - 注册免费账户

### 步骤 2: 设置 SharePoint List

1. **使用公司邮箱登录 SharePoint**
2. **创建 SharePoint List**
   - 列表名称：`US-China News Articles`
   - 字段：
     - Title (文本，必需)
     - URL (文本)
     - Date (日期时间)
     - Outlet (文本)
     - Headline (文本)
     - NutGraph (多行文本)
     - Category (文本)
     - Nested (文本)

3. **设置权限**
   - 内部人员可读
   - 只有你的账号可以写入

### 步骤 3: 更新代码以使用 SharePoint

代码已经创建了 `sharepoint_integration.py`，需要：

1. **安装依赖**
   ```bash
   pip install Office365-REST-Python-Client
   ```

2. **配置凭证**
   - 在 Streamlit Secrets 或环境变量中设置：
     ```toml
     [sharepoint]
     site_url = "https://yourcompany.sharepoint.com/sites/YourSite"
     username = "your.email@company.com"
     password = "your-password-or-app-password"
     ```

3. **更新定时任务**
   - 修改 `daily_collector_to_sheets.py` 使用 SharePoint

### 步骤 4: 在 Tableau Desktop 中连接 SharePoint

1. **打开 Tableau Desktop**
2. **连接到数据**
   - 选择 "Microsoft SharePoint Lists"
   - 输入 SharePoint 站点 URL
   - 使用公司账号登录

3. **选择 List**
   - 选择 "US-China News Articles" List

4. **创建可视化**
   - 设计仪表板
   - 添加交互式筛选器

### 步骤 5: 发布到 Tableau Public

1. **在 Tableau Desktop 中**
   - 点击 "Server" → "Tableau Public" → "Save to Tableau Public"
   - 登录 Tableau Public 账户
   - 数据会提取并上传到 Tableau Public

2. **设置自动刷新（可选）**
   - 在 Tableau Desktop 中设置数据提取刷新计划
   - 或手动定期刷新

## 代码迁移步骤

### 1. 安装 SharePoint 依赖

```bash
pip install Office365-REST-Python-Client
```

### 2. 更新 requirements.txt

添加：
```
Office365-REST-Python-Client>=2.3.0
```

### 3. 创建 SharePoint 版本的 daily collector

创建 `daily_collector_to_sharepoint.py`（基于 `daily_collector_to_sheets.py`）

### 4. 更新 Streamlit 应用

修改 `app_with_sheets_db.py` 以支持 SharePoint

## 配置示例

### Streamlit Secrets (`.streamlit/secrets.toml`)

```toml
[sharepoint]
site_url = "https://yourcompany.sharepoint.com/sites/YourSite"
username = "your.email@company.com"
password = "your-password"
list_name = "US-China News Articles"
```

### 环境变量（用于定时任务）

```bash
export SHAREPOINT_SITE_URL="https://yourcompany.sharepoint.com/sites/YourSite"
export SHAREPOINT_USERNAME="your.email@company.com"
export SHAREPOINT_PASSWORD="your-password"
export SHAREPOINT_LIST_NAME="US-China News Articles"
```

## 关于 Tableau Public 个人账号

### ✅ 可以使用个人账号

- Tableau Public 是免费的
- 可以使用个人账号
- 数据会公开（这是 Tableau Public 的限制）

### 展示作品的优势

- ✅ 可以分享链接给任何人
- ✅ 可以嵌入到 WordPress
- ✅ 可以展示你的数据分析能力

### 注意事项

- ⚠️ 数据会公开（这是 Tableau Public 的限制）
- ⚠️ 如果需要私有数据，需要使用 Tableau Online（付费）

## 完整工作流程

1. **数据收集**（GitHub Actions 定时任务）
   - 每天自动收集新闻文章
   - 上传到 SharePoint List

2. **数据存储**（SharePoint - 公司账号）
   - 内部人员可见
   - 实时更新

3. **数据分析**（Tableau Desktop - 个人账号）
   - 连接 SharePoint
   - 创建可视化
   - 发布到 Tableau Public

4. **展示**（Tableau Public - 个人账号）
   - 公开链接
   - 可以嵌入 WordPress
   - 展示作品

## 总结

- ✅ **可以使用个人 Tableau Public 账号**
- ✅ **数据存储在公司的 SharePoint**（内部可见）
- ✅ **Tableau Public 用于展示**（公开）
- ⚠️ **需要 Tableau Desktop** 作为中间工具（连接 SharePoint 并发布到 Tableau Public）

需要我帮你：
1. 完成代码迁移到 SharePoint？
2. 创建 `daily_collector_to_sharepoint.py`？
3. 更新 Streamlit 应用以支持 SharePoint？

