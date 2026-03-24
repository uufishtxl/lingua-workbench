# 功能通信总线：pwa_pomodoro

> **说明**：此文档为 AI 与开发者之间的 API 契约和开发状态同步总线。
> 新功能开发前，务必将此模板复制至 `_ai_design/features/feature_[name].md` 后再进行填写与开发。

## 1. 架构与契约 (Feature Specification)
> **人类主导，AI 辅助梳理。未定死契约且未被确认前，禁止编写实际的 API View 或 Vue 代码。**

- **业务目标与背景**: 
  - 建立一个与原 `frontend` 并行的纯移动端 PWA（`mobile_pwa`），基于 Vue3 + Vite。
  - 主要实现 Pomodoro（番茄钟）工具的沉浸式原生体验，支持添加到手机主屏幕，无浏览器地址栏干扰（Standalone）。
  - 后续支撑外网访问请求打回到家庭内网的 DRF Django 数据中心（配合 Tailscale 或 Cloudflare Tunnels）。
  - **核心迁移与复刻**：必须完整复刻网页版右下角的 `PomodoroWidget` 逻辑，包含：
    - 正面计时器（工作流、休息流、SuperFlow 无缝连接）。
    - Category (Tag) 悬浮切换矩阵。
    - 带有拉尺 (Ruler) 的专注时长选择。
    - 3D 翻转到背面的 `PomodoroHistory` (带备注修改、月历日历弹窗导航、周视图)。
    - 未完成会话 (Ongoing Session) 的拦截恢复对话框。
- **依赖关联 constraints**: 
  - 与 `frontend` 同级的独立目录：`mobile_pwa`。
  - **UI 约束**: 彻底抛弃 PC 端宽屏思维，强制要求纯实用类（Tailwind CSS）竖屏响应式开发。但风格上必须继承原有网页 Widget 强烈的“Neumorphism (拟物拟态/软 UI)” 质感。
  - **状态管理**: 使用 Pinia 持久化（如 `pinia-plugin-persistedstate`）记录 `timeLeft`, `isRunning` 等，复刻 `pomodoroStore.ts` 的逻辑。
  - **PWA 插件**: 需集成 `vite-plugin-pwa`，并配置相应的 Manifest 和 App Icons。
- **API 契约草案 (JSON Draft)**
  - 根据目前 `backend/pomodoro/models.py` 与 `frontend/src/api/timerApi.ts` 的实际实现，完全沿用当前后端已经稳定成熟的 API 契约（无需让后端改代码，这是纯前端重构迁移）：
  - **Endpoints 包含**:
    - `GET /v1/pomodoro-tags/` 
    - `POST /v1/pomodoros/` (创建 started 会话)
    - `PATCH /v1/pomodoros/<id>/` (更新状态 complete/interrupted，更新 task 笔记)
    - `GET /v1/pomodoros/ongoing/` (检查意外断层的未完结会话)
    - `GET /v1/pomodoros/history/?date=YYYY-MM-DD` 
    - `GET /v1/pomodoros/earliest/`

---

## 2. 前端实现状态 (Frontend Pass)
- **当前进度**: 🔵已完成
- **AI 留言板 (问题反馈 / 联调诉求)**: 
  - [已完成创建、脚手架依赖安装、`vite.config.ts`, `manifest` 编写和原文件迁移(`pomodoroStore.ts`, `PomodoroWidget.vue`, 等等）。]
  - [UI 逻辑和动画都已按照移动端独立模式更新并解决 Typescript 类型问题。添加了极简 Login 页提供鉴权支持。现可供测试！]

---

## 3. 后端精准实现状态 (Backend Pass)
- **当前进度**: �已完成 (免开发)
- **后端执行约束记录**: 
  - [由于后端 DRF Api 与 Models 早已竣工并能被原 Web Frontend 强韧使用，针对本 PWA 计划，后端基本免去了开发。只需确保后续测试环境可以跨域联调。]
