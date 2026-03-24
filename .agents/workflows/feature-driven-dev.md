---
description: 执行特性驱动的 AI 开发流 (Feature-Driven AI Dev)，强制 API 契约优先
---

# Feature-Driven Development 工作流

每当要求开发新页面、新模块或重大重构时，**必须调出并严格执行此流程。** 本流程意图打破 Vibe Coding 的急躁感与冗余，通过在 AI 对话之间传递和使用“通信总线 (Feature Bus)”文档，实现前后端精确收敛。在执行本流程前，无论用户怎么要求快，必须步步为营。

## 第一阶段：基建与对齐准则 (Alignment)

1. 使用工具读取 `_ai_design/core_architecture.md` 文件。
2. 将该文件内的内容（Core Domain Models 和 诸如 **禁用原生 CSS，强制使用 Tailwind** 的铁律）作为本次会话的**核心最高准则**挂载在当前工作内存里。绝不允许违背。

## 第二阶段：创建通信白板并梳理契约 (Specification)

1. 向人类询问一个简短且具有代表性的“英文特征名”（例如：`dashboard_charts`）。
2. 将 `_ai_design/templates/feature_bus_template.md` 拷贝为 `_ai_design/features/feature_[特征名].md`，如 `_ai_design/features/feature_dashboard_charts.md`。
3. **关键拦截**：开始充当人类的架构副手，辅助填写上述文档中的 **“1. 架构与契约 (Feature Specification)”**。
   - **绝对禁止编写 .vue, .py 等具体业务代码**，哪怕你已经迫不及待觉得自己知道了怎么写。
   - 在人类未对 Request Body 或 Response JSON 的精简必要字段表示确认前，不得进入下一开发阶段。

## 第三阶段：前端开发 (Frontend Pass)

> 当第一阶段（契约）在文档中落笔并获得人类首肯后，进入前端开发态（如果是纯后端任务，则跳过此阶段）：

1. 每次编写组件代码或 API 请求，必须严格遵从 `feature_[特征名].md` 记录的契约交互（无论它多简略，都是事实依据）。
2. 在新功能中应用 **严格的 Tailwind 实用类规范**。
3. 当遇到契约不足（比如忽然需要某个原定没有的字段来丰富 UI 图标）或依赖后端的场景时，不用中断前端进度，先写 Mock 或容错。
4. 将这些痛点问题更新到 `feature_[特征名].md` 的 **“2. 前端实现状态 - AI 留言板”** 中，状态改为 **已完成**。

## 第四阶段：后端开发 (Backend Pass)

> 如果是另一轮断层会话，必须从第一阶段开始复习上下文。但如果是在流程连贯执行中进入本阶段：

1. **强读取** `feature_[特征名].md` 的契约需求及前端 AI 留言板的痛点。
2. 约束自身编写 DRF 的行为：
   - 绝不允许拿一个涵盖 30 个字段的大型通用 Serializer 发送给只需求 3 个特征值的前端。
   - 利用 Django ORM （譬如 `values()`, `annotate()`, `select_related()`）精确命中并只响应所需字段组合，防止过度获取（Over-fetching）。
3. 当且仅当接口完全调通、符合契约（或在留言板基础上拓展的部分）后，将文档中的 **“3. 后端精准实现状态”** 修改为 **已完成**。
