# AI 如何根据反馈学习？

## 🔍 工作原理

### 1. 反馈保存

当你标记一篇文章为"不正确"并选择正确类别时：
- 反馈保存到 `classification_feedback.json`
- 格式示例：
```json
{
  "article_url": {
    "status": "incorrect",
    "headline": "China rolls out red carpet as Thailand's king makes first official visit",
    "summary": "...",
    "current_category": "Geopolitics",
    "correct_category": "US Multilateralism",
    "timestamp": "2025-11-13T10:00:00"
  }
}
```

### 2. 反馈如何被使用

在每次 API 分类时（`api_classifier.py` 第 277-298 行）：

1. **读取反馈文件**
   ```python
   feedback_file = Path("classification_feedback.json")
   if feedback_file.exists():
       # 读取所有反馈
   ```

2. **提取"incorrect"反馈**
   ```python
   # 只使用"incorrect"的反馈，因为这是用户明确指出的错误分类
   for url, feedback in feedback_data.items():
       if feedback.get('status') == 'incorrect' and feedback.get('correct_category'):
           headline = feedback.get('headline', '')
           correct_cat = feedback.get('correct_category', '')
           # 转换为示例格式
           user_feedback_examples.append(f'- "{headline}" → {correct_cat}')
   ```

3. **添加到 Prompt 中**
   ```python
   user_feedback_text = ""
   if user_feedback_examples:
       user_feedback_text = f"\n\nUser feedback examples (recent corrections - use these to improve accuracy):\n" + "\n".join(user_feedback_examples[-10:])  # 只使用最近10个反馈
   ```

### 3. Prompt 结构

最终的 prompt 包含：
1. 类别说明
2. 分类规则
3. 原始示例（75个）
4. **用户反馈示例**（你提供的修正）
5. 要分类的文章

## 📝 具体例子

### 你的例子："China rolls out red carpet as Thailand's king makes first official visit"

**场景**：
- 原始分类：可能是 "Geopolitics" 或其他类别
- 你标记为：不正确
- 你选择正确类别：`US Multilateralism`

**学习过程**：

1. **反馈保存**：
   ```json
   {
     "https://example.com/article": {
       "status": "incorrect",
       "headline": "China rolls out red carpet as Thailand's king makes first official visit",
       "current_category": "Geopolitics",
       "correct_category": "US Multilateralism"
     }
   }
   ```

2. **下次分类时，Prompt 会包含**：
   ```
   User feedback examples (recent corrections - use these to improve accuracy):
   - "China rolls out red carpet as Thailand's king makes first official visit" → US Multilateralism
   ```

3. **AI 看到这个示例后**：
   - 理解：类似"中国接待外国领导人"的新闻应该归类到 "US Multilateralism"
   - 学习：双边外交访问、国家间关系属于多边主义类别
   - 应用：下次遇到类似文章时，会参考这个示例进行分类

## 💡 关键点

### 1. Few-Shot Learning（少样本学习）

这不是"训练"模型，而是：
- 在每次分类时，将你的反馈作为**示例**添加到 prompt 中
- AI 看到这些示例，学习"类似情况应该这样分类"
- 这是一种**上下文学习**（In-Context Learning）

### 2. 只使用"incorrect"反馈

代码中只使用 `status == "incorrect"` 的反馈：
- "correct"反馈不添加（因为已经是正确的，不需要学习）
- "incorrect"反馈明确指出了错误，需要学习正确的分类

### 3. 只使用最近10个反馈

```python
user_feedback_examples[-10:]  # 只使用最近10个反馈
```

原因：
- Prompt 长度限制
- 最近的反馈更相关
- 避免 prompt 过长导致成本增加

## 🔄 学习效果

### 立即生效

- 反馈保存后，**下一次分类就会生效**
- 不需要重新训练模型
- 不需要重启应用

### 累积学习

- 每次反馈都会累积
- 反馈越多，分类越精准
- 但只保留最近10个（避免 prompt 过长）

## 📊 实际效果示例

**第一次分类**（没有反馈）：
- "China rolls out red carpet as Thailand's king makes first official visit"
- AI 可能分类为：`Geopolitics` 或 `Inside China`

**你提供反馈后**：
- 标记为不正确，选择 `US Multilateralism`

**第二次分类**（有反馈）：
- 遇到类似文章："China hosts Indonesian president for state visit"
- AI 看到你的反馈示例，会参考：
  - "中国接待外国领导人" → `US Multilateralism`
  - 因此可能分类为：`US Multilateralism`

## ⚠️ 注意事项

1. **不是真正的"训练"**
   - 模型参数没有改变
   - 只是通过 prompt 中的示例来指导分类
   - 每次分类都是独立的 API 调用

2. **反馈只在本地生效**
   - `classification_feedback.json` 在本地
   - 云端版本需要单独配置

3. **反馈数量限制**
   - 只使用最近10个反馈
   - 如果反馈超过10个，旧的会被忽略

