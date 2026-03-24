# Lingua Workbench - Core Architecture & Global Rules

## 1. 严格的技术栈铁律 (Strict Tech Stack Rules)
这些铁律**不可动摇**，任何 AI 和开发者在生成代码前必须遵守：
- **Styling (前端样式)**: 严格使用 **Tailwind CSS** 实用类 (Utility Classes) 控制样式。**绝对禁止**在 `.vue` 文件的 `<style>` 标签中手写 Vanilla CSS，除非遇到 Tailwind 无法覆盖的极其复杂的定制化动画或不可复用的三方件覆盖。
- **DRF / Django / 后端服务**: 
  - 严禁为了图省事把大而全的 Serializer 喂给仅仅需要两三个字段的前端。务必审视 API 的 Over-fetching 问题。使用 `.values()` 或专门的 LightSerializer 提炼数据。
  - ORM 查询应当贯彻 Pythonic / Django 风格，充分利用反向查询 (`related_name`) 和 `.select_related()` / `.prefetch_related()` 防治 N+1 问题。
  - **LLM 实例创建**：绝不允许在代码中自说自话创建和硬编码大模型实例（例：`ChatOpenAI(api_key=...)`）。必须严格读取 `settings.LLM_CONFIG` 中的约束（如 `default`, `sound_script`, `article_meta`）进行调度和初始化。

## 2. 核心领域模型 (Core Domain Models)
- **Audio Hierarchy (音频结构)**:
  - `Drama` (剧集)
    - -> `SourceAudio` (音频源，通过 `drama`, `season`, `episode` 定位)
      - -> `AudioChunk` (长音频切块，属于 SourceAudio)
        - -> `AudioSlice` (精细切片，包含高亮难点，属于 AudioChunk)
- **Review System (复习系统)**:
  - `ReviewCard` (复习卡片): 关联到 `AudioSlice`，内置基于 5 个 Box 的简单 Leitner 算法进行 spaced repetition。

## 3. 已存在的公用组件 (Common Modules / Services)
- **前端 (Vue 3 + Tailwind)**: 
  - (待补充：未来遇到可复用的 UI 积木，如 Modal, AudioPlayer 请登记于此)
- **后端服务 (Services)**:
  - `slice_source_to_chunks`: 负责底层大文件的分段。
  - `batch_translate_texts`: 负责批量调用大模型进行英文切片的中文翻译。
