# 功能通信总线：English Corner (沉浸式英语角)

> **说明**：此文档为 AI 与开发者之间的 API 契约和开发状态同步总线。

## 1. 架构与契约 (Feature Specification)

- **业务目标与背景**: 
  - 提供一个沉浸式的英语口语/书面练习环境。
  - 核心组件：全屏 3D/2D 知识图谱 (ECharts)、浮动对话面板。
  - 功能：基于场景 (Scenario) 的 AI 对练、实时高亮已知词汇、划词提取新词至图谱。

- **依赖关联 constraints**: 
  - **前端**: Vue 3 + Tailwind CSS (严格遵守实用类规范)。
  - **后端**: Django + DRF。
  - **模型关联**: 需关联 `phrase_log.PhraseLog` (用于同步 Mastery 和 Box Level)。
  - **LLM**: 严格从 `settings.LLM_CONFIG` 获取配置。

- **API 契约草案 (JSON Draft)**

  ### 1.1 获取场景列表 (Scenarios)
  - **Endpoint**: `GET /api/english_corner/scenarios/`
  - **Response Payload**:
    ```json
    [
      {
        "id": 1,
        "title": "Starbucks Ordering",
        "description": "Practice ordering coffee in a busy cafe.",
        "icon": "☕",
        "vibe": "Busy, friendly"
      }
    ]
    ```

  ### 1.2 获取知识图谱数据 (Knowledge Graph)
  - **Endpoint**: `GET /api/english_corner/graph/`
  - **Response Payload**:
    ```json
    {
      "nodes": [
        {
          "id": "1",
          "label": "Coffee",
          "type": "keyword",
          "mastery": 85,
          "box_level": 5,
          "explanation": "A caffeinated drink...",
          "example": "I need a coffee."
        }
      ],
      "links": [
        { "source": "1", "target": "2", "relation": "synonym" }
      ]
    }
    ```

  ### 1.3 提交提取词汇 (Word Extraction)
  - **Endpoint**: `POST /api/english_corner/extract/`
  - **Request Body**:
    ```json
    {
      "text": "momentum",
      "scenario_id": 1,
      "context_sentence": "Keep your momentum going."
    }
    ```

---

## 2. 前端实现状态 (Frontend Pass)
- **当前进度**: 🔵已完成 (基于 Mock 数据)
- **AI 留言板**: 
  - [DONE] 已完成全屏遮罩、ECharts 集成、划词高亮、Scenario 切换逻辑。
  - [TODO] 待对接后端真实接口后，需清理 `mockGraphData`。
  - [ISSUE] 前端 `VocabRichText` 依赖 `WordNode` 数组进行分词，后端 Response 务必保持字段一致。

---

## 3. 后端精准实现状态 (Backend Pass)
- **当前进度**: 🟢待启动
- **后端执行约束记录**: 
  - 必须使用 `english_corner` App。
  - 务必利用 `values()` 优化 `KnowledgeGraphView`，避免发送冗余的 DB 字段。
  - 提取词汇时应检查 `phrase_log` 是否已存在该词，避免重复创建。
