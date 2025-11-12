### 1. 📖 前端专属 Epic：Audio Slicer (UI/UX 总结)

这是你所有前端页面的功能、UI 和逻辑的最终版蓝图。

#### 侧边栏导航 (`el-menu`)

- **`Audio Slicer` (父级)**
    
    - **`Load Source`** (加载源) [路径: `/slicer/load-source`]
        
    - **`Workbench`** (工作台) [路径: `/slicer/workbench/:chunk_id`]
        
    - **`Clip Library`** (切片库) [路径: `/slicer/clip-library`]
        

#### 页面 A: `Load Source` (加载源)

![[audio_slicer.load_source__upload.png]]
![[audio_slicer.load_source__select_chunk.png]]


- **UI (基于 `image_a3613c.png`)**
    
    - **`el-select` x 3**: "Drama", "Season", "Episode" (V1 `allow-create`)。
        
    - **`el-upload` (上传框)**: (基于 `image_a3609b.png`)，默认隐藏。
        
    - **`Chunk Grid` (切片网格)**: (基于 `image_a3613c.png` 的 `001, 002...` 按钮)，默认隐藏。
        
    - **`el-button`**: `[ Start Editing Chunks ]` (默认禁用)。
        
- **界面逻辑 (State Machine)**
    
    1. **联动**：用户填写三个 `el-select`。
        
    2. **API 触发**: 当三个值都**非空**时，**立即**触发 API (`GET /api/source_audio/?...`) 去“查找”这个源。
        
    3. **状态 A (404 / 未找到)**:
        
        - API 返回 404。
            
        - **显示** `el-upload` (上传框)。
            
        - **上传**: 用户上传 40MB 的 `SourceAudio`。
            
        - **后端自动触发**: 后端收到文件后，**自动**开始 `ffmpeg`“预切片”任务，生成 20-45 个 `AudioChunk`。
            
        - **前端轮询**: 前端显示 "Processing... (0/45)"，直到后端返回“切片完成”。
            
        - **切换状态**: 完成后，自动进入“状态 B”。
            
    4. **状态 B (200 / 已找到)**:
        
        - API 返回 200，并附带所有关联的 `AudioChunk` 列表。
            
        - **显示** "Chunk 网格"。
            
        - `Chunk` 按钮根据 `chunk.has_slices` 属性显示**灰色** (未切过) 或**白色** (已切过)。
            
- **跳转逻辑**
    
    1. 用户在 "Chunk 网格" 中点击一个 `Chunk` (例如 `006`)，该按钮**变为蓝色** (选中)。
        
    2. `[ Start Editing Chunks ]` 按钮被**激活**。
        
    3. 用户点击该按钮。
        
    4. **全屏跳转**: `router.push('/slicer/workbench/6')`。
        

#### 页面 B: `Workbench` (工作台)

![[audio_slicer.workbench.png]]

- **UI (基于 `image_a3c5fc.png`)**
    
    - **顶部**: `wavesurfer.js` 波形图实例。
        
    - **中部**: `Selected Regions` (暂存区) 列表，这是一个 `el-table` 或 `div v-for`。
        
    - **底部**: `[ 💾 Save Slices ]` 按钮。
        
- **界面逻辑 (State Logic)**
    
    1. **加载 (`onMounted`)**:
        
        - 从 URL 中读取 `chunk_id: 6`。
            
        - **API (1)**: `GET /api/audiochunks/6/` (获取 60s 的 MP3 URL)。
            
        - **API (2)**: `GET /api/audioslices/?chunk_id=6` (获取**已存在**的 Clips)。
            
    2. **渲染**:
        
        - `wavesurfer.js` 加载 60s 的 MP3。
            
        - `Selected Regions` (暂存区) 列表**初始为空**。
            
        - `wavesurfer.js` 调用 `addRegion()`，把 API (2) 返回的**已存 Slices** 在波形图上用**灰色**、**不可编辑**的区域画出来。
            
    3. **创建 (核心交互)**:
        
        - 用户在**空白处**拖拽，`wavesurfer.js` 创建一个**新的、蓝色**的 `Region`。
            
        - `region-created` 事件触发。
            
        - **立即** `push` 一个**新对象** (`{ id: null, ... }`) 到“暂存区”列表。
            
        - “暂存区”列表响应式地渲染出一个**新的表单行**。
            
    
    - **填表**:
        
        - **V1 (手动)**: 用户手动填写 `Original Text` 和 `Notes`。
            
        - **V2 (自动)**: (我们讨论的 V2) `region-created` 事件触发时，自动 `GET /api/transcript/?time=...` 并填充 `Original Text`。
            
        - **Tags**: 用户从 `el-select` (多选, `allow-create`) 中选择或创建 "病因" 标签 (e.g., "Flap T", "H-Deletion")。
            
    - **保存**:
        
        - 用户点击 `[ 💾 Save Slices ]`。
            
        - 前端遍历“暂存区”数组，`POST` 所有**新条目** (`id: null`) 到后端 API (`POST /api/audioslices/create_batch/`)。
            
        - 保存成功后，清空“暂存区”，并将波形图上的蓝色区域变为灰色。
            

#### 页面 C: `Clip Library` (切片库)

![[audio_slicer.clip_library.png]]

- **UI (基于 `image_b2593e.jpg`)**
    
    - **顶部 (Filter 区)**: “多维筛选”栏。
        
        - `el-select` x 4: "Drama", "Season", "Episode", "Chunk" (均可不选，即 "All")。
            
        - `el-select` (Tags): 多选 "病因" 标签 (e.g., "Flap T")。
            
        - `el-input` (Keyword): 搜索 `Original Text` 和 `Notes`。
            
        - `el-button` (Search): 触发搜索。
            
    - **中部 (Training / Mirror 区)**: “发音镜”面板。
        
        - 永久可见，包含两个 `wavesurfer.js` 实例 ("Audio Slice:" 和 "Your voice:")。
            
        - 包含 `[✨ AI Chat]` 按钮。
            
    - **底部 (Regions / Table 区)**: `el-table` 显示筛选结果。
        
- **界面逻辑 (State Logic)**
    
    1. **筛选**: 用户在“Filter 区”设置条件，点击 `[Search]`。
        
    2. **API 调用**: `GET /api/clips/?drama=...&chunk=...&search=...&tags=...`
        
    3. **渲染**: `el-table` (底部) 被 API 返回的数据填充。
        
    4. **激活 (核心交互)**:
        
        - 用户点击**底部 `el-table`** 中的**任一行**。
            
        - **中部 "发音镜"** 被激活。
            
        - “发音镜”的 `Original Text` (字幕) 被填充。
            
        - “发音镜”的“Audio Slice:”波形图**加载**该切片的 MP3。
            
    5. **训练 (发音镜)**:
        
        - 用户点击 `[🔴 Record]`。
            
        - 前端使用 `MediaRecorder` API (纯浏览器) 录音。
            
        - 录音结束，`Blob` 被加载到 "Your voice:" 波形图中，用于上下对比。
            
        - 此过程**不**涉及后端。
            
    6. **编辑 (行内编辑)**:
        
        - (我们之前讨论的) 用户点击**底部 `el-table`** 中的 `Original Text` 或 `Notes` 单元格。
            
        - 单元格变为 `el-input`。
            
        - 修改完毕 `onBlur` (失去焦点) 时，**立即**触发 `PATCH /api/audioslices/{id}/` 保存。
            
    7. **分析 (AI Chat)**:
        
        - 用户在“发音镜”面板点击 `[✨ AI Chat]`。
            
        - 弹出一个 `el-dialog` 聊天框，预设好上下文（原文、音频），调用 `POST /api/slicer/ask-ai/`。

### 2. 🗂️ 开发用 Epic / Stories / Tasks

这是你的全栈“敏捷开发看板”。

#### **Epic: Audio Slicer (V1)**

- **目标**: 打造一个基于“预切片”架构的，集“创建、浏览、训练”于一体的语言学习工作台。
    

#### **Story #1: # [Audio Slicer > Core/Backend] 创建三级模型与 ffmpeg 引擎服

- **目标**: 搭建所有功能的数据模型和核心后端服务。
- **Tasks**:
    - [x] **[Task/DB]**: 在 `slicer` app 中创建 `SourceAudio` 模型 (`drama`/`season`/`episode`/`path`/`uploaded_at`)。
    - [x] **[Task/DB]**: 创建 `AudioChunk` 模型 (FK to `SourceAudio`, `chunk_index`, `file` [60s MP3], `has_slices` [Boolean])。
    - [x] **[Task/DB]**: 创建 `AudioSlice` 模型 (FK to `AudioChunk`, `start_time`, `end_time`, `file` [like 5s MP3], `original_text`, `notes`, `tags` [JSONField])。
    - [x] **[Task/Backend]**: 创建一个 `ffmpeg` 服务，`slice_source_to_chunks(source_audio)`，使用 `ffmpeg` 循环（60秒“一刀切”）创建 `AudioChunk`。
    - [x] **[Task/Backend]**: 创建另一个 `ffmpeg` 服务，`slice_chunk_to_slice(chunk, start, end)`，用于创建最终的 `AudioSlice`。
    - [x] **[Task/Backend]**: 将 `slice_source_to_chunks` 挂载到 `SourceAudio` 的 `post_save` 信号上，实现上传后自动“预切片”。

#### **Story #2: [Audio Slicer > Feature] Load Source 页面**
- **目标**: 实现一个允许用户上传 `SourceAudio` 或加载现有 `AudioChunk` 的入口。   
- **Tasks**:
    - [ ] **[Task/API]**: `POST /api/source_audio/` (处理 40MB 大文件上传)。
    - [ ] **[Task/API]**: `GET /api/source_audio/lookup/` (用于“三级下拉框”的查询)。
    - [ ] **[Task/API]**: `GET /api/audiochunks/?source_id=...` (用于填充“Chunk 网格”)。
    - [ ] **[Task/Frontend]**: 构建 `LoadSource.vue` 页面。
    - [ ] **[Task/Frontend]**: 实现“三级下拉框”的 `watch` 和 API 联动逻辑。
    - [ ] **[Task/Frontend]**: 实现“状态 A (上传)”和“状态 B (Chunk 网格)”的 UI 切换。
    - [ ] **[Task/Frontend]**: 实现 `[Start Editing]` 按钮的 `router.push('/slicer/workbench/:id')` 跳转。
#### **Story #3: [Audio Slicer > Feature] `Workbench` 页面 

- **目标**: 实现一个基于波形图的“批量切片创建”界面。
    
- **Tasks**
    - [ ] **[Task/API]**: `GET /api/audioslices/?chunk_id=...` (用于加载“灰色”已存区域)。
    - [ ] **[Task/API]**: `POST /api/audioslices/create_batch/` (接收一个**列表**，在后端循环调用 `slice_chunk_to_slice` 服务并创建 `AudioSlice`)。
    - [ ] **[Task/Frontend]**: 构建 `Workbench.vue` 页面，并安装 `wavesurfer.js`。
    - [ ] **[Task/Frontend]**: `onMounted` 时，从 URL 加载 `chunk_id`，获取 MP3 URL，并加载 `wavesurfer.js`。
    - [ ] **[Task/Frontend]**: 实现“加载灰色区域”逻辑。
    - [ ] **[Task/Frontend]**: 实现“`region-created` -> `push` 到暂存区列表”的核心交互。
    - [ ] **[Task/Frontend]**: 构建“暂存区”列表的 UI，包括 `el-input` (Notes) 和 "病因" 标签的 `el-select` (多选, `allow-create`)。
    - [ ] **[Task/Frontend]**: 实现 `[Save Slices]` 按钮的 `POST` 逻辑和成功后的 UI 刷新。

#### **Story #4: [Audio Slicer > Feature] `Clip Library` 页面

- **目标**: 实现一个集“浏览、筛选、精听、跟读”于一体的“终极仪表盘”。
    
- **Tasks**:
    - [ ] **[Task/API]**: 增强 `GET /api/clips/` (即 `AudioSlice` 列表)，使其支持所有“多维筛选”参数 (`drama`, `chunk`, `search_keyword`, `tags__contains`...)。
    - [ ] **[Task/Frontend]**: 构建 `ClipLibrary.vue` 页面 (基于 `image_b2593e.jpg`)。
    - [ ] **[Task/Frontend]**: 构建顶部的“多维筛选”栏，并实现 `[Search]` 按钮的 API 调用。
    - [ ] **[Task/Frontend]**: 构建底部的 `el-table` (Regions 列表)。
    - [ ] **[Task/Frontend]**: 构建中部的“发音镜” (Pronunciation Mirror) 组件（两个 `wavesurfer` 实例）。
    - [ ] **[Task/Frontend]**: 实现核心交互：点击`Table` -> `Mirror` 加载数据。
    - [ ] **[Task/Frontend]**: 集成 `MediaRecorder` API 到 `[🔴 Record]` 按钮，实现“跟读对比”。
    - [ ] **[Task/Frontend]**: (V1.5) 实现 `el-table` 的“行内编辑”功能 (`onClick` -> `el-input` -> `onBlur` -> `PATCH`)。

### 3. 知识点总结 (Backend Knowledge Points)

1.  **文件上传核心流程**: `models.FileField` 负责定义存储，`ViewSet` 中的 `parser_classes = [MultiPartParser]` 负责解析 `multipart/form-data` 请求，`ModelViewSet` 负责处理整个创建逻辑。
2.  **Model 核心知识**:
    *   **外键 (`ForeignKey`)**: 用于建立模型间的关联。
    *   **联合唯一约束 (`unique_together`)**: 保证多个字段的组合值是唯一的（如：同一剧集只能有一个 `SourceAudio`）。
3.  **定制 `ModelViewSet`**:
    *   重写 `perform_create` 方法，在保存模型时自动关联当前登录的 `user`。
    *   重写 `get_queryset` 方法，根据 `request.user` 实现数据权限隔离。
4.  **`@action` 装饰器**: 在标准的 `ViewSet` 之外，创建自定义的 URL 和方法，如 `create_batch`，以处理非标准的业务需求。
5.  **`ffmpeg` 命令行调用**:
    *   **`segment`**: 用于将一个大文件按固定时长（如60秒）分割成多个小文件 (`AudioChunk`)。
    *   **`-ss` 和 `-to`**: 用于从一个文件中精确截取某个时间段的内容，创建 `AudioSlice`。
    *   **`-c copy`**: 流复制模式，在不需要重新编码时极大提高处理速度。
6.  **Django Signals (`post_save`)**: 实现事件驱动的逻辑解耦。当一个 `SourceAudio` 模型被保存后，自动触发一个信号，通知 `slice_source_to_chunks` 服务开始执行“预切片”任务。
7.  **服务层抽象 (`services.py`)**: 将核心业务逻辑（如调用 `ffmpeg`）封装成独立的服务函数，使 `views.py` 保持简洁，并让逻辑本身更易于复用和测试。
8.  **ORM 跨关系查询**: 在 `get_queryset` 中使用双下划线 `__` (如 `source_audio__user`) 来实现跨模型的关联查询，这是 Django ORM 的一个强大功能。
9.  **序列化器的批量处理 (`many=True`)**: 在 `create_batch` 视图中，通过在序列化器上设置 `many=True`，使其能够验证和反序列化一个对象列表，是实现批量创建接口的关键。
10. **Python `subprocess` 模块**: 使用 `subprocess.run` 执行外部命令，并通过 `check=True` 和 `capture_output=True` 进行错误捕获和输出管理。
11. **Python `tempfile` 模块**: 使用 `tempfile.TemporaryDirectory` 来安全地处理中间文件（如 `AudioChunk`），确保这些临时文件在操作完成后被自动清理。