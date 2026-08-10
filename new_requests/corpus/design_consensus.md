# 📚 教材语料加工（Corpus Pipeline）+ 教材学习（跟读练习）设计共识

> 由 grill-me 逐项拷问后达成的共识。作为后续 to-issues 拆分与实现的唯一依据。
> 设计稿见同目录 `corpus_*.png`（以本共识为准，设计稿冲突处按共识裁决）。

---

## 0. 功能定位

双端功能：
- **加工端（教师）**：上传教材 PDF → 按 Unit 提取结构化语料（6 模块）→ 人工校准 7 大知识点 → 导出复习提纲 PDF / 练习卷 / 默写卷。
- **学习端（学生）**：教材学习页选 年级/学期/Unit → 跟读练习（整段 TTS 音频 + whisper 时间戳逐句高亮）。

复用既有平台：侧边栏布局（AppLayout）、认证、文件存储、Huey 任务队列、SQLite、`generate_tts_audio`（TTS 共用函数，reader 已在复用）。

---

## 1. 数据模型

### 1.1 Textbook（新增表，全局共享，个人项目不按用户隔离）

| 字段 | 类型 | 说明 |
|---|---|---|
| id | UUID | 主键 |
| name | VARCHAR | 教材名（如 "5A新版五上"） |
| grade / semester | VARCHAR | 年级/学期（学习页"选 年级/学期"用） |
| pdf_file | FileField | → `media/textbooks/` |
| parsed_pages | JSONB | 全书页面文本数组缓存（pdfplumber 一次解析，后续 Unit 任务复用） |
| words_region_pages | JSONB | 书末词表区域页范围（见 §6） |
| words_by_unit | JSONB | 词表按 Unit 归类结果缓存（`{unit: [words]}`，LLM 一次归类全书） |
| parsed_at | TIMESTAMP | |

- 既有 `backend/english_book_5a.pdf` 通过种子脚本注册为第一条 Textbook。

### 1.2 corpus_tasks（新增表）

| 字段 | 类型 | 说明 |
|---|---|---|
| id | UUID | 主键 |
| name | VARCHAR | 任务名（如 "5A新版五上 · Unit 2"） |
| textbook | FK → Textbook | |
| unit | INTEGER | 单元号 |
| status | ENUM | draft / proofreading / completed |
| stage | INTEGER | 0-3 |
| created_at / updated_at | TIMESTAMP | |
| raw_pages | JSONB | **原始 page 级提取文本（不可变）**，清洗/分桶可重算但此物永覆盖 |
| cleaned_modules | JSONB | 6 模块清洗后文本（LLM 归整产物） |
| knowledge_points | JSONB | 7 大知识点（AI 预填 + 人工编辑） |
| tts_audio_url | VARCHAR | 学习页整段音频（Gemini） |
| tts_timestamps | JSONB | whisper 时间戳映射（句子级） |
| extract_status / bucket_status / kp_status / tts_status / paper_status | VARCHAR | pending / running / done / error |
| extract_error / ... | TEXT | 各阶段错误信息 |
| practice_paper_* / dictation_* | 文件/时间 | 练习卷/默写卷产物（学生版+教师版） |

### 1.3 cleaned_modules（6 模块，忠实教材原文结构）

1. Topic words — 单元内生词
2. Fun time — 含 Sound 子内容（自然拼读）
3. Talking time — 含 Find the rule 子内容（语法归纳）
4. Story time
5. Project — 含 Step by step 指南 + Big Task 范文
6. Words to use — 书末词表按 Unit 归类切片

> 与 trials 原型（7 模块含独立 grammar_tip）的关系：grammar_tip 并入 Talking time。

### 1.4 knowledge_points（7 大板块，教学派生视图）

1. 词汇 — **Topic words + Words to use 合并**（Q2 定）
2. 短语 — MVP 预填空（用户后续摸索规律再补）
3. 句型 — MVP 预填空
4. 语法 — Find the rule 必填预填 + 用户自补（介词/时态/连词）
5. 拼读 — Fun time 的 Sound（每 Unit 一个字母/组合）
6. 梗概 — 由 Story time 生成
7. Big Task 范文 — 由 Project 的 Step by step 内容提取

> LLM 输入 = 本单元 cleaned_modules + 书末词表归类结果；输出 = 7 KP 预填 JSON，**Human 增删改**。

---

## 2. 状态机（Q5 定）

| stage | 含义 | status |
|---|---|---|
| 0 | 提取完成（触发 `extract_unit` 任务） | draft |
| 1 | 总览（自动跳转） | draft |
| 2 | 脏预览（6 Tab 只读） | draft |
| 3 | 校准（"进入校准" → `llm_bucket` + `generate_kps`） | proofreading |

- **保存**（任意一次，右栏有内容）→ 解锁导出；**手动"完成校订"** → completed（终态标记，之后编辑自动退回 proofreading）。
- 导出条件：status != draft。
- **回退**：任意阶段可回退重跑（改 Unit 重新提取）；raw_pages 不可变，清洗/分桶可重算。
- 仪表盘"继续" = 跳到当前 stage；"编辑" = 进校准页。
- 删除任务 = 级联清理媒体文件（TTS/PDF 产物）。

---

## 3. 页面与路由（Q12 定）

| 页面 | 路由 |
|---|---|
| 任务仪表盘 | `/corpus/dashboard` |
| Stage 0 提取 | `/corpus/extract` |
| Stage 1 总览 | `/corpus/overview/:taskId` |
| Stage 2 脏预览 | `/corpus/preview/:taskId` |
| Stage 3 校准 | `/corpus/calibrate/:taskId` |
| 教材学习（选择+跟读，单页内切换） | `/corpus/learn` |

菜单（AppLayout menuItems）：
```
Corpus 语料加工（顶级）
├── 任务仪表盘      /corpus/dashboard
├── 新建任务        /corpus/extract
└── 教材学习        /corpus/learn
```

---

## 4. 核心流程与 UI 裁决

### Stage 0：提取触发
- 拖拽/选教材（Textbook 选择器）+ **Unit 输入框** + "开始提取" → 提取队列（huey）。
- 页面顶部标记当前 Unit。

### Stage 1：总览
- 统计卡片：Total Characters / Modules Identified / Page Coverage / Words to Use 数量。
- 6 模块芯片列表。

### Stage 2：脏预览
- **6 个 Tab**（Topic/Fun/Talking/Story/Project/Words to use）只读脏文本（机械粗分桶结果）。
- **不做** [Line Break Error] 错误标记（C3 裁决：砍掉）；保留固定说明文字（"以下为机械粗分桶结果，可能包含噪声"）。

### Stage 3：校准（双栏）
- 左栏（45%）"原文 / Read-Only Source"：**6 个 Tab**（含 Words to use）只读滚动。
- 右栏（55%）"知识点"：**7 个 KP 垂直手风琴（Vertical Accordian）**，点开一个 = **大 Textarea 编辑**（C2 裁决）。
- 每 Tab：**AI 修复/重新生成按钮 + 可选指令输入框**（placeholder："描述你希望如何调整此模块，可留空"）→ LLM 重算 → **diff 确认** → 应用/丢弃。左栏修复只改对应模块，不连锁重算 KP（Q6b 定）。
- 底部：Back to Extraction / Export PDF / Generate Exercises / **Generate 默写卷按钮**（C6 定）。

### 仪表盘
- 顶部"上传教材 PDF，提取结构化语料并生成知识点"快速开始横幅 → Stage 0。
- 统计卡片：总任务数 / 已完成 / 进行中 / 覆盖单元数。
- 任务表：任务名 / 状态标签（草稿灰、校订中蓝、已完成绿）/ 模块进度（x/6）/ 知识点进度（x/7）/ 创建时间 / 操作（继续/编辑/导出/删除；草稿无导出）。

---

## 5. 学习页面（教材学习，Q7 定）

- 入口：菜单"教材学习" → 选 年级/学期（Textbook）→ Unit（corpus_tasks）→ 跟读模式。
- 模块 Tab：**Fun / Talking / Story / Project 四模块**提供整段播放 + 句子随时间戳高亮 + 点击句子跳转播放；**Topic words / Words to use 只展示文本，无音频**（标注"无音频"）。
- TTS 输入只含四模块正文（Topic/Project 的 Step by step 指导文字朗读价值低，筛掉——待最终拍板，倾向筛掉只留范文正文）。

---

## 6. 词表（Words to use）提取策略（Q10b 定）

- **废弃** trials 的"首次→最后出现页"算法（mock 数据已证坏：目录页 "Topic words" 列标题误触发，抓到全书 6-96 页）。
- 新算法：从**书末往前找最后一次出现**的 "Words to use / Word list" 类标题 → 区域 = 该页 → 最后一页；**排除前 1/4 页**（目录区）。
- 双栏：pdfplumber 按 x 坐标分组，左栏→右栏阅读顺序拼接。
- Page break 断行：整页提取不丢字，Unit 边界混入相邻词由 LLM 容错（宁可多抓不漏抓）。
- 归类：**整段词表一次交给 LLM 按 Unit 归类**（输出 `{unit: [words]}`）→ 缓存 Textbook.words_by_unit → Unit 任务直接读缓存。
- 兜底：归类结果进左栏 Words to use Tab（可 AI 修复）+ 右栏词汇 KP 人工增删改。

---

## 7. 导出（Q8 定）

### 复习提纲 PDF
- WeasyPrint 确定性渲染：教材/Unit 头部 + 7 KP 板块排版。
- 同步返回，每次结果一致。

### 练习卷（异步 huey 生成，一次出学生版 + 教师版两份 PDF）
题型 ↔ KP 映射：
| KP | 题型 |
|---|---|
| 词汇 | 听力题（卷面印朗读原文，老师自读；另附 edge-tts 音频清单）+ 词汇填空（中文提示） |
| 拼读 | 语音辨析题（相近音归类） |
| 词汇/短语 | 句子填空（中文提示） |
| 语法 | 单选题 |
| 句型 | 句型转换 / 多空格填空 |
| 梗概 | Story time 复述题 |
| Big Task | 写作题 |

- 听力音频：**edge-tts 生成**（免费无限额），PDF 首页"听力音频清单"（题号 → 文件名），题目处标"听录音 N"（U1 定）。
- 不加配分/题量配置，每板块固定 N 题，"再生成"换一批。
- 覆盖式保留最近一份 + 记录生成时间。

### 默写卷
- **确定性渲染**（不调 LLM）：词汇/短语/句型 KP → "中文提示 + 空格"格式，双版本（学生版空白 + 教师版答案）。

---

## 8. TTS 策略（双 provider，Q8c/d 定）

| 用途 | Provider | 说明 |
|---|---|---|
| 学习页整段音频 | **Gemini**（`generate_tts_audio`，一天 10 次免费） | completed 后生成一次 + 缓存复用；whisper 本地对齐句子时间戳 |
| 练习卷听力题 | **edge-tts**（免费无限额） | 无时间戳需求，整段播放 |

- 抽 `tts_service` 抽象层按用途路由 provider。
- 候选国产 TTS（备用）：CosyVoice2（国产开源需 GPU）、MiniMax Speech（国产 API）。edge-tts 为免费首选。

---

## 9. 异步任务切分（Q10 定）

| 任务 | 触发 | 产物 |
|---|---|---|
| `extract_unit` | Stage 0 | 全书解析缓存（首次）+ Unit 页提取 + 机械清洗 + 机械粗分桶 → stage=1 |
| `llm_bucket` | "进入校准" | DeepSeek 归整 6 模块 → cleaned_modules |
| `generate_kps` | llm_bucket 完成后链式 | DeepSeek 7 KP 预填 |
| `generate_tts` | completed 后 | Gemini 整段音频 + whisper 对齐 |
| `generate_practice_paper` | "生成练习" | DeepSeek 题型 JSON + edge-tts 听力音频 + WeasyPrint 双 PDF |
| 复习提纲 / 默写卷 | 按钮 | 同步确定性渲染 |

- 任务状态存 corpus_tasks（各 `*_status`/`*_error`），前端**轮询**状态接口。
- 所有任务可重跑覆盖产物；raw_pages 永不变。

---

## 10. 错误处理与可靠性

- Unit 越界（找不到 "Unit N" 标记）→ 任务报错提示。
- 扫描版 PDF（无文本层，`has_text_layer` 检测）→ 提示"需 OCR"中止。
- 词表区域找不到 → 降级：词汇 KP 只用 Topic words + 警告。
- DeepSeek JSON 稳定性（trials 已知坑）：先 `response_format=json_object`，异常去掉重试一次；解析容忍代码围栏/前后杂字。

---

## 11. 待验证风险清单（开发中标记）

1. **词表区域新算法**（书末反向找标题 + 排除前 1/4 页）需在真实 5A PDF（Windows 环境）验证——CID 字体容器跑不了。
2. 双栏按 x 坐标分栏提取效果需真实书验证。
3. 学习页 whisper 对齐（Gemini TTS 音频 → whisper segments → difflib 匹配已知句子）需实测。
4. Gemini 一天 10 次免费 quota 是否够用（每 Unit 一次，6 单元教材 = 6 次/本，可接受）。
5. edge-tts 英文朗读质量"试试"。

---

## 12. 验收标准（6 条）

1. 上传/选择教材（Textbook 表，含年级/学期），Stage 0 输入 Unit 号建任务 → 提取该 Unit 分模块文本（机械清洗 + 粗分桶）。
2. Stage 1 统计卡片 + Stage 2 六 Tab 脏预览 + Stage 3 左六 Tab 只读原文 / 右七 KP 垂直手风琴大文本框编辑（AI 预填 + 指令修复 + diff 确认）。
3. 保存 KP → 解锁导出复习提纲 PDF（WeasyPrint 确定性渲染）。
4. 生成练习卷（学生版/教师版：听力题印朗读原文 + edge-tts 音频清单、语音辨析、填空、单选、句型转换、复述、写作）+ 默写卷（双版本）。
5. 教材学习页：选 年级/学期/Unit → Fun/Talking/Story/Project 四模块逐句跟读（Gemini 整段音频 + whisper 时间戳高亮 + 点击跳转）。
6. 仪表盘正确显示统计、状态、模块进度（x/6）、知识点进度（x/7）。

---

## 13. 开发模式

- **AI 在容器写代码（语法/逻辑校验）→ 用户在 Windows venv 真机测试**（容器无 pdfplumber 等依赖）。
- 后端单测：清洗/分桶规则用 fixture 文本、LLM 全 mock（DeepSeek/Gemini/edge-tts）、状态机、API 端点。
- PDF 相关留 Windows 冒烟脚本（真实 5A 书验证，对应 §11 风险项）。
- 前端：路由 + 校准页（编辑/保存/diff）+ 学习页（音频高亮/跳转）组件测试，TDD 红-绿-重构，与既有 app tests.py 模式一致。

---

## 14. 下一步

- 用 to-issues skill 按 Epic 拆分开发任务（数据层/UI/LLM 集成/导出/学习页）。
- 按 §11 风险项安排 Windows 验证冒烟脚本。
