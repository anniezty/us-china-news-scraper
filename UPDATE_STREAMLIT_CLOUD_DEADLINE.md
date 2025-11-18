# 如何更新 Streamlit Cloud 测试阶段截止时间

## 问题
当前 Streamlit Cloud 上的配置还是旧的 `"2025-11-17"`，导致测试阶段已经结束。

## 解决方案

### 步骤 1: 登录 Streamlit Cloud
1. 访问 https://share.streamlit.io/
2. 登录你的账户

### 步骤 2: 进入应用设置
1. 找到你的应用
2. 点击应用旁边的 **"⋮"**（三个点）菜单
3. 选择 **"Settings"** 或 **"Manage app"** → **"Settings"**

### 步骤 3: 更新 Secrets
1. 在设置页面，找到 **"Secrets"** 标签页
2. 找到 `[test_mode]` 部分
3. 修改 `deadline` 的值：

**选项 A: 如果你想要 UTC 时间 11/18 17:00**
```toml
[test_mode]
enabled = true
password = "test2025"
deadline = "2025-11-18 17:00"
```

**选项 B: 如果你想要本地时间（EST）11/18 17:00**
EST 下午 5 点 = UTC 晚上 10 点（EST 是 UTC-5）
```toml
[test_mode]
enabled = true
password = "test2025"
deadline = "2025-11-18 22:00"
```

**选项 C: 如果你想要本地时间（PST）11/18 17:00**
PST 下午 5 点 = UTC 第二天凌晨 1 点（PST 是 UTC-8）
```toml
[test_mode]
enabled = true
password = "test2025"
deadline = "2025-11-19 01:00"
```

### 步骤 4: 保存并重新部署
1. 点击 **"Save"** 按钮
2. Streamlit Cloud 会自动重新部署应用
3. 等待部署完成（通常 1-2 分钟）

### 步骤 5: 验证
1. 刷新应用页面
2. 应该可以正常访问（需要输入密码）

## 时区对照表

| 本地时间 | 时区 | UTC 时间 |
|---------|------|---------|
| 11/18 17:00 EST | UTC-5 | 11/18 22:00 UTC |
| 11/18 17:00 PST | UTC-8 | 11/19 01:00 UTC |
| 11/18 17:00 UTC | UTC+0 | 11/18 17:00 UTC |

## 注意事项

- Streamlit Cloud 使用 **UTC 时间**
- 配置中的 `deadline` 会被视为 **UTC 时间**
- 如果你想要本地时间，需要手动转换为 UTC

## 快速检查

更新后，错误信息应该显示新的截止时间，例如：
- `deadline: 2025-11-18 17:00 UTC`（如果设置为 UTC 时间）
- `deadline: 2025-11-18 22:00 UTC`（如果设置为 EST 下午 5 点）

