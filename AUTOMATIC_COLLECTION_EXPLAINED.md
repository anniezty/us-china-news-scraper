# 自动收集新闻到 Google Sheets 说明

## ✅ 好消息：关闭 Cursor 不会影响自动收集！

**Cursor 只是一个代码编辑器**，关闭它**不会**影响自动收集功能。

## 🔄 自动收集的工作原理

### 1. 定时任务（Launchd）

你的系统已经配置了定时任务：
- **任务名称**：`com.uschina.dailycollector`
- **运行方式**：通过 macOS 的 `launchd` 系统在后台运行
- **独立性**：**完全独立**于 Cursor 编辑器

### 2. 定时任务如何工作

```
macOS 系统 (launchd)
    ↓
每天定时触发
    ↓
运行 daily_collector_to_sheets.py
    ↓
抓取新闻 → 上传到 Google Sheets
```

**关键点**：
- ✅ 定时任务由 **macOS 系统**管理，不是 Cursor
- ✅ 即使关闭 Cursor，定时任务**仍然运行**
- ✅ 即使关闭电脑，下次开机后定时任务**自动恢复**
- ✅ 不需要手动操作，完全自动化

## 📋 当前配置状态

根据检查，你的系统已经有定时任务在运行：
- ✅ `com.uschina.dailycollector` - 每日收集任务

## 🔍 如何确认定时任务正在运行？

### 方法 1：检查 launchd 任务
```bash
launchctl list | grep uschina
```

如果看到任务名称，说明任务已加载。

### 方法 2：查看日志
```bash
# 查看最近的日志
tail -f logs/daily_collector.log
```

### 方法 3：检查 Google Sheets
- 打开 Google Sheets
- 查看是否有新的文章被自动添加
- 检查日期是否是最新的

## ⚠️ 什么情况下会影响自动收集？

### ❌ 会影响的情况：

1. **电脑完全休眠（系统休眠）**
   - 如果电脑进入深度休眠，定时任务**不会**在休眠期间运行
   - ⚠️ **重要**：系统唤醒后，**不会**自动执行错过的任务
   - 解决方案：见下面的"休眠处理方案"

2. **电脑完全关机**
   - 如果电脑关机，定时任务不会运行
   - 但下次开机后会自动恢复

3. **删除或修改定时任务配置**
   - 如果删除了 launchd plist 文件
   - 如果修改了脚本路径或环境变量

4. **网络问题**
   - 如果网络连接失败，收集会失败
   - 但下次运行时会重试

### ✅ 不会影响的情况：

1. **屏幕关闭（显示器休眠）**
   - 如果只是屏幕关闭，但系统还在运行
   - 定时任务**仍然会运行** ✅
   - macOS 可以在屏幕关闭时继续运行后台任务

2. **关闭 Cursor 编辑器** ✅
   - Cursor 只是编辑器，不影响定时任务

3. **关闭终端窗口** ✅
   - 定时任务在后台运行，不依赖终端

4. **关闭浏览器** ✅
   - 自动收集不依赖浏览器

5. **关闭 Streamlit 应用** ✅
   - Streamlit 应用和定时任务是独立的

### ✅ 不会影响的情况：

1. **关闭 Cursor 编辑器** ✅
   - Cursor 只是编辑器，不影响定时任务

2. **关闭终端窗口** ✅
   - 定时任务在后台运行，不依赖终端

3. **关闭浏览器** ✅
   - 自动收集不依赖浏览器

4. **关闭 Streamlit 应用** ✅
   - Streamlit 应用和定时任务是独立的
   - 定时任务只负责收集，不依赖 Streamlit

## 🔧 如何管理定时任务？

### 查看定时任务状态
```bash
launchctl list | grep uschina
```

### 手动运行一次（测试）
```bash
cd /Users/tingyuzheng/Projects/us_china_picker
bash scripts/run_daily_collector.sh
```

### 查看定时任务日志
```bash
# 查看日志文件
tail -f logs/daily_collector.log

# 或查看系统日志
log show --predicate 'process == "daily_collector_to_sheets.py"' --last 1h
```

### 停止定时任务（如果需要）
```bash
launchctl unload ~/Library/LaunchAgents/com.uschina.dailycollector.plist
```

### 重新启动定时任务
```bash
launchctl load ~/Library/LaunchAgents/com.uschina.dailycollector.plist
```

## 📊 定时任务配置

### 脚本位置
- **主脚本**：`daily_collector_to_sheets.py`
- **运行脚本**：`scripts/run_daily_collector.sh`
- **配置文件**：`config_en.yaml`

### 收集的新闻来源
默认收集以下来源的新闻：
- nytimes.com
- scmp.com
- ft.com
- apnews.com
- washingtonpost.com
- reuters.com

### 上传位置
- **Google Sheets ID**：`1Cltg8pq-jhtgR6_lysW-gNIe9JSKOh2vCT4Pxo7pcpA`
- **Sheet 名称**：按周分组（例如：`Week 2025-11-11 to 2025-11-18`）

## 🆚 Cursor vs 定时任务

| 项目 | Cursor 编辑器 | 定时任务 |
|------|--------------|---------|
| **作用** | 编辑代码 | 自动收集新闻 |
| **运行方式** | 手动打开 | 系统后台自动运行 |
| **依赖关系** | 无 | 无 |
| **关闭影响** | 不影响定时任务 | 不影响 Cursor |
| **是否需要** | 编辑代码时需要 | 一直运行 |

## 💤 电脑休眠时的行为

### 不同休眠状态的区别

| 状态 | 系统是否运行 | 定时任务是否运行 | 说明 |
|------|------------|----------------|------|
| **屏幕关闭** | ✅ 是 | ✅ **是** | 只是显示器休眠，系统还在运行 |
| **轻度休眠** | ✅ 是 | ✅ **是** | 系统进入节能模式，但仍在运行 |
| **深度休眠** | ❌ 否 | ❌ **否** | 系统完全休眠，定时任务暂停 |
| **完全关机** | ❌ 否 | ❌ **否** | 系统关闭，定时任务停止 |

### ⚠️ 重要：深度休眠的影响

**当前配置**：使用 `StartCalendarInterval`（在特定时间点触发）

**行为**：
- ✅ 如果电脑在定时任务执行时间**之前**唤醒，任务会正常执行
- ❌ 如果电脑在定时任务执行时间**期间**休眠，任务**不会**执行
- ❌ 如果电脑在定时任务执行时间**之后**才唤醒，**不会**自动执行错过的任务

**你的定时任务时间**：
- 每天 08:07
- 每天 15:07
- 每天 23:37

### 🔧 休眠处理方案

#### 方案 1：保持电脑不深度休眠（推荐）

在"系统设置" → "电池" → "选项"中：
- 关闭"防止电脑在显示屏关闭时自动进入睡眠"
- 或设置"永不"进入睡眠（仅限连接电源时）

#### 方案 2：使用网络唤醒（Wake on LAN）

如果电脑支持，可以配置网络唤醒，在定时任务时间自动唤醒电脑。

#### 方案 3：使用云服务器（最可靠）

考虑将定时任务迁移到：
- **GitHub Actions**（免费，每天运行）
- **云服务器**（AWS、Google Cloud 等）
- **Streamlit Cloud**（如果支持定时任务）

#### 方案 4：手动补充收集

如果错过了定时任务，可以手动运行：
```bash
cd /Users/tingyuzheng/Projects/us_china_picker
python3 daily_collector_to_sheets.py
```

## 💡 总结

**关闭 Cursor 不会影响自动收集！**

- ✅ 定时任务由 macOS 系统管理
- ✅ 完全独立于 Cursor 编辑器
- ✅ 即使关闭 Cursor，定时任务仍然运行
- ✅ 即使关闭电脑，下次开机后自动恢复

**关于休眠：**
- ✅ **屏幕关闭**：不影响，定时任务仍然运行
- ⚠️ **深度休眠**：会影响，错过的任务不会自动执行
- 💡 **建议**：保持电脑不深度休眠，或使用云服务器

**你只需要：**
1. 确保定时任务已配置（✅ 已完成）
2. 确保电脑在定时任务时间**不深度休眠**
3. 定期检查 Google Sheets 确认收集正常

**不需要：**
- ❌ 保持 Cursor 打开
- ❌ 保持终端打开
- ❌ 保持浏览器打开
- ❌ 手动运行脚本（除非电脑休眠错过了任务）

## 🔍 如何验证自动收集是否工作？

1. **检查 Google Sheets**
   - 打开 Google Sheets
   - 查看最新的 sheet
   - 确认有今天的文章

2. **查看日志文件**
   ```bash
   tail -20 logs/daily_collector.log
   ```

3. **手动运行一次测试**
   ```bash
   cd /Users/tingyuzheng/Projects/us_china_picker
   python3 daily_collector_to_sheets.py
   ```

