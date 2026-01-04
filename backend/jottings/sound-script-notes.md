# Sound Script 开发笔记

## 日期: 2025-12-31

---

## 1. Human-in-the-Loop 方案

### 核心流程
```
用户输入句子 → LLM 生成 Sound Script → 前端展示 → 用户修正 → 保存修正结果
                                                          ↓
                                                  积累为 few-shot 样例
```

### 实现阶段

**阶段 1（现阶段）- 不改前端**
- LLM 输出 → 手动检查 → 把好例子存到 JSON 文件
- 下次运行时作为 few-shot 放进 prompt

**阶段 2 - 前端参与**
- 前端展示 LLM 结果
- 提供编辑按钮让用户修正字段
- 保存反馈到后端数据库
- 简单的 👍👎 反馈标记

**阶段 3 - 利用反馈**
- Few-shot: 把高质量的 (input, corrected_output) 对作为 prompt 示例
- RAG: 检索与当前输入相似的历史 case
- 微调: 积累足够多后做模型微调

---

## 2. Few-shot 解释

### 什么是 Few-shot？
在 prompt 里给 LLM **几个示例**，让它学着照做。

| 方式 | 说明 |
|------|------|
| Zero-shot | 只给指令，不给例子 |
| Few-shot | 给指令 + 1~3个例子 |

### 示例结构
```
## EXAMPLE
Input:
- Full Context: "I'm going to get him."
- Focus Segment: "going to get him"
- Speed Profile: "native_fast"

Output:
{
    "phonetic_tags": ["Reduction", "Elision"],
    "script_segments": [
        {"original": "going to", "sound_display": "gunna", ...},
        {"original": "him", "sound_display": "im", ...}  # h 脱落
    ]
}

## NOW ANALYZE THE USER'S INPUT:
```

### 效果
LLM 看到 `"him" → "im"` 的例子后，会更容易学会在快速语流中省略弱读音。

---

## 3. 当前待解决的问题

- [ ] LLM 输出的 "You've" 没有体现 v 音脱落
- [ ] 考虑在 prompt 中加入 few-shot 例子来引导更准确的音变识别

---

## 4. 下一步建议

1. 手动收集几个典型 case（包括修正后的版本）
2. 在 prompt 里加 1-2 个 few-shot 例子
3. 验证效果后再考虑前端编辑功能
