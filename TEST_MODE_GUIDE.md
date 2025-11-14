# 测试阶段访问控制指南

## 📋 功能说明

这个功能允许你在部署到云端后，控制应用的访问权限。适合用于：
- 让同事测试一次后自动下线
- 设置测试截止日期
- 使用密码保护测试版本

## 🔧 配置方式

### 方式 1: Streamlit Secrets（推荐 - 云端部署）

在 Streamlit Cloud 的 Secrets 中添加：

```toml
[test_mode]
enabled = true
password = "test2025"  # 测试密码
deadline = "2025-12-31"  # 测试截止日期（可选）
```

### 方式 2: 环境变量（本地测试）

```bash
export TEST_MODE_ENABLED="true"
export TEST_PASSWORD="test2025"
export TEST_DEADLINE="2025-12-31"  # 可选
```

## 📝 使用场景

### 场景 1: 只让同事测试一次

**设置：**
```toml
[test_mode]
enabled = true
password = "test2025"
deadline = "2025-11-15"  # 设置一个短期截止日期
```

**效果：**
- 同事需要输入密码才能访问
- 11月15日后自动禁用，无法访问

### 场景 2: 密码保护，无时间限制

**设置：**
```toml
[test_mode]
enabled = true
password = "test2025"
deadline = ""  # 留空，不设置时间限制
```

**效果：**
- 需要输入密码才能访问
- 没有时间限制，可以一直使用

### 场景 3: 时间限制，无密码

**设置：**
```toml
[test_mode]
enabled = true
password = ""  # 留空，不需要密码
deadline = "2025-12-31"
```

**效果：**
- 不需要密码，直接访问
- 12月31日后自动禁用

### 场景 4: 完全禁用测试模式（生产环境）

**设置：**
```toml
[test_mode]
enabled = false
```

或者直接删除 `[test_mode]` 配置

**效果：**
- 任何人都可以访问，无限制

## 🚀 部署到云端后的操作

### 启用测试模式

1. 在 Streamlit Cloud 的 Secrets 中添加：
```toml
[test_mode]
enabled = true
password = "你的测试密码"
deadline = "2025-11-20"  # 测试截止日期
```

2. 应用会自动重启，启用测试模式

### 禁用测试模式（测试结束后）

**方法 1: 修改 Secrets**
```toml
[test_mode]
enabled = false
```

**方法 2: 删除 test_mode 配置**
直接删除 `[test_mode]` 部分

**方法 3: 设置过期日期**
```toml
[test_mode]
enabled = true
deadline = "2025-11-14"  # 设置为过去的日期
```

## 💡 最佳实践

1. **测试阶段**：
   - 设置密码 + 短期截止日期
   - 例如：`password = "test2025"`, `deadline = "2025-11-20"`

2. **正式上线**：
   - 设置 `enabled = false` 或删除配置
   - 任何人都可以访问

3. **临时维护**：
   - 设置一个很短的截止日期
   - 例如：`deadline = "2025-11-13"`（今天）

## 🔐 安全提示

- **不要将密码提交到 GitHub**
- 使用 Streamlit Cloud Secrets 存储敏感信息
- 测试结束后及时禁用测试模式
- 定期更换测试密码

## 📊 配置优先级

1. Streamlit Secrets（最高优先级）
2. 环境变量
3. 默认值（测试模式禁用）

## ❓ 常见问题

**Q: 如何让同事测试一次后自动下线？**
A: 设置一个短期截止日期，例如 `deadline = "2025-11-15"`

**Q: 测试结束后如何重新启用？**
A: 修改 `deadline` 为未来日期，或设置 `enabled = false` 后重新启用

**Q: 可以同时使用密码和时间限制吗？**
A: 可以，两者可以同时启用

**Q: 本地开发时如何禁用测试模式？**
A: 不设置环境变量，或设置 `TEST_MODE_ENABLED=false`

