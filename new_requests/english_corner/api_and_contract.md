# 🌐 English Corner: AI 场景对话练习功能设计协议

> **设计初衷**：利用 LLM 实现高度沉浸、具备即时反馈的“回合制”英语口语/文本对话练习。

---

## 1. 核心业务主干 (Business Logic)

- **场景双轨制**：
  - **角色一 (Tutor)**：英语指导老师，负责对用户的输入进行 Polish（润色）、纠错并给出中文解析。
  - **角色二 (Character)**：场景设定角色（如 Senior Engineer），负责推动剧情。
- **划词制卡**：用户在前端对地道表达式划词，后端调用 LLM 生成结构化卡片（Prompt Q & Answer），存入 SRS 系统。
- **SRS 复习**：基于 Leitner System (Box 1-5)，支持“英文提示 -> 心中/手动拼写 -> 结果反馈”的循环复习逻辑。
- **异步处理**：利用 **Huey Task** 处理耗时的 Whisper 识别、LLM 双角色生成及 Gemini TTS 生成，保证 API 响应不阻塞。

---

## 2. 技术栈契约 (Tech Stack Contract)

- **LLM/TTS**: **Gemini 2.5 Flash** (通过 `google-genai` SDK)。
  - **白嫖方案**: 使用 Gemini 2.5 Flash 进行文本生成，随后使用 `gemini-2.5-flash-preview-tts` 进行原生音频合成。
- **Backend**: Django (REST Framework) + Huey (Task Queue)。
- **Frontend**: Vue 3 + 现有 Reader/ReviewCard 组件 hooks。
- **Audio Output**: 24kHz, 16-bit, Mono WAV (由后端通过 `wave` 模块封装 RIFF 头)。

---

## 3. API 接口契约 (API First)

### 3.1 场景管理 (Scenarios)
- `GET /api/scenarios/`: 获取场景卡片列表（包含 `icon`、图片、标题、难度）。
- `POST /api/scenarios/`: 创建自定义场景。
  - **Payload**: `{"title", "description", "icon"}`
  - **黑魔法 (Backend Magic)**: 后端会根据 `title` 和 `description` (Vibe) 自动合成 `prompt` 字段作为场景专属 System Prompt。

### 3.2 会话管理 (Conversations)
- `POST /api/conversations/`: 选中场景并开启。后端返回第一条 AI 语音破冰消息。
- `GET /api/conversations/{id}/`: 获取会话详情，包括由 Agent 动态生成的会话 `summary`（阶段性滚动总结）。

### 3.3 交互逻辑 (Messages)
- `POST /api/conversations/{id}/messages/`: 发送语音/文本。
  - **Response (202 Accepted)**: 返回 `message_id`。
- `GET /api/conversations/{id}/messages/{message_id}/`: 获取消息处理进度与结果。
  - **作用**: 前端用于轮询（Polling）或查询具体结果。
  - **字段**: 
    - `id`, `role`, `status`, `is_processed`, `timestamp`
    - `user_content` (仅 User 消息)
    - `tutor_feedback` (仅 User 消息，异步生成): `{"polished_text", "explanation_cn"}`
    - `character_reply` (仅 AI 消息): `{"content", "audio_url"}`
  - **工作流**: 
    1. 前端 `POST` 后拿到 ID。
    2. 前端监控 `status` 或 `is_processed`。
    3. 状态变为 `SUCCESS` 时渲染结果；若为 `FAILED` 则提示用户重试。

### 3.4 划词与复习 (Review)
- `POST /api/flashcards/generate/`: 划词触发。Payload: `{"message_id", "text"}`。后端实时调用 LLM 生成结构化复习题。
- `GET /api/review/today/`: 获取今日到期卡片。

---

## 4. 数据库建模 (Data Model Draft)

- **Scenario**: 存储场景定义的 Prompts, Roles, Images, Icons。
- **Conversation**: 存储会话状态、归属用户、动态 Summary。
- **PracticeMessage**: 核心流水表。存储 role, rawContent, tutorFields, characterFields, isProcessed, status (PENDING/SUCCESS/FAILED)。
- **PracticeFlashcard**: 存储 targetPhrase, promptQuestion, exampleContext 以及 SRS 指标（boxLevel, nextReviewAt）。
- **WordRelationship**: (New) 存储词汇间的关联关系。字段：`source_id`, `target_id`, `relation_type` (synonym, context, etc.)。
- **WordNode (Updated)**:
  - `embedding`: `vector(1536)` (New) - 存储语义向量，用于计算词汇间的语义相似度并自动触发连线。

---

### 3.5 知识图谱 (Knowledge Graph) - (New)
- `GET /api/relationship-graph/`: 获取当前用户所有划词的关系图谱数据。
  - **Response**: 
    ```json
    {
      "nodes": [
        {"id": "1", "label": "tank the performance", "type": "phrase", "explanation": "...", "example": "..."},
        {"id": "2", "label": "Daily Stand-up", "type": "topic", "explanation": "...", "example": "..."}
      ],
      "links": [
        {"source": "1", "target": "2", "relation": "context"}
      ]
    }
    ```

---

## 5. 待办/疑难点 (Backlog)

- [ ] **Token 节约策略**: 采用存储全量 DB，但发送给 LLM 时使用“最近 4-6 轮滑动窗口”的模式。**必须确保每次请求的第 0 项（System Instruction）永远包含 Scenario 的全局 Prompt 和角色设定**，防止 AI 长期对话后“出戏”。
- [ ] **Shadow Reading (跟读功能)**: 
  - UI 侧在 Character Reply 旁边提供录制按钮。
  - 支持用户录制并对比原声与自己的发音。
  - 数据存储：初期可暂存浏览器 Blobs，或追加一个 `user_shadow_audio` 字段上传至后端。
- [ ] **语音格式与清理**: 
  - 确保生成的音频 URL 在多端（Web/Mobile）兼容播放。
  - **清理策略**: 设定长周期的自动清理任务（例如：`AUDIO_RETENTION_DAYS = 365`），而非由于空间焦虑导致的即时清理。
- [ ] **高亮逻辑复用**: 确保 `reader` 模块中的划词交互可以无缝迁移到会话 UI 中。

---

> **状态**：已冻结设计，待开发。
> **最后更新日期**：2026-03-11
