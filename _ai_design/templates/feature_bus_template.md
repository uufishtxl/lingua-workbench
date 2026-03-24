# 功能通信总线：[功能名称]

> **说明**：此文档为 AI 与开发者之间的 API 契约和开发状态同步总线。
> 新功能开发前，务必将此模板复制至 `_ai_design/features/feature_[name].md` 后再进行填写与开发。

## 1. 架构与契约 (Feature Specification)
> **人类主导，AI 辅助梳理。未定死契约且未被确认前，禁止编写实际的 API View 或 Vue 代码。**

- **业务目标与背景**: 
  - (例：用户需要在一个页面下拉选择剧集，加载该集所有分片，并在界面高亮播放)
- **依赖关联 constraints**: 
  - (例：需复用现有 AudioChunk 模型，需基于 Tailwind 实现新的时间轴组件)
- **API 契约草案 (JSON Draft)**
  - **Endpoint**: `[GET / POST / PUT / DELETE] /api/...`
  - **Request (Params/Body)**: 
    ```json
    {
      "key": "value"
    }
    ```
  - **Response Payload (按需严格剪裁)**:
    ```json
    {
      "id": 1,
      "exact_field_needed": "example"
    }
    ```

---

## 2. 前端实现状态 (Frontend Pass)
- **当前进度**: 🟢待启动 / 🟡开发中 / 🔵已完成 
- **AI 留言板 (问题反馈 / 联调诉求)**: 
  - [例：写 UI 时发现缺少 "user_avatar" 字段，为了避免中断，我先用了占位符。请后端在接下来实现时将其加入契约 Response 中。]

---

## 3. 后端精准实现状态 (Backend Pass)
- **当前进度**: 🟢待启动 / 🟡开发中 / 🔵已完成
- **后端执行约束记录**: 
  - [要求：基于上面的需求和留言板，后端精简 View 和 Serializer，杜绝塞入不必要数据。]
  - [例：我抛弃了长序列化器，通过 `.values()` 查询只返回了必需字段。]
