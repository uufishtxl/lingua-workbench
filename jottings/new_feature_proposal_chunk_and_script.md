# New Propsal

现在你有两个选择：

重新导入（会自动删除旧数据）：
POST /api/scripts/ingest/
Body: { "season": 10, "episode": 13 }
只删除不导入：
DELETE /api/scripts/clear/?season=10&episode=13

---


## 🎯 开发目标：实现“剧本流伴随与动态切分”功能 (Script Side Panel & Relay Workflow)

**项目背景**：在现有的 Audio Slicer Workbench 中，新增一个右侧面板，用于展示从网页抓取的整集剧本。用户通过“接力棒”模式（Relay Mode），在学习过程中手动将剧本切分给后续的 Audio Chunk。


# Feature Spec: Script Side Panel & Workflow

## 1. 核心概念 (Core Concept)

一个伴随音频切片学习的 **“流式剧本阅读器”**。

- **初始状态**：整集剧本全部挂载在第 1 个 Chunk 下。
    
- **交互模式**：用户在学习过程中，手动“剪切”剧本，将剩余部分“推”给下一个 Chunk（接力棒模式）。
    
- **数据结构**：结构化存储，分离“对白”与“动作/场景”，支持复习高亮和音频弱关联。
    

---

## 2. 数据库设计 (Data Model)

文件: `scripts/models.py`

```Python
class ScriptLine(models.Model):
    # --- 1. 定位与顺序 ---
    # 归属的大任务/Chunk。初始全部指向该集第一个Chunk，随用户操作更新。
    chunk_id = models.ForeignKey('AudioChunk', on_delete=models.CASCADE, related_name='script_lines')
    # 绝对顺序 (0, 1, 2...)，保证渲染顺序
    index = models.IntegerField(db_index=True)

    # --- 2. 类型与内容 ---
    TYPE_CHOICES = [
        ('dialogue', '对话'),      # 有人说话
        ('action',   '独立动作'),  # 没人说话的纯动作行
        ('scene',    '场景标题'),  # [Scene: ...]
    ]
    line_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='dialogue')

    speaker = models.CharField(max_length=100, null=True, blank=True)
    
    # 核心展示文本 (Clean Text)。
    # dialogue: "Watch me!" (不含动作)
    # action/scene: 完整内容
    text = models.TextField()

    # 附属动作 (Metadata)。
    # 仅当 dialogue 中穿插动作时使用，如 "he drinks milk"
    action_note = models.TextField(null=True, blank=True)

    # 原始文本 (Backup)
    raw_text = models.TextField()
    zh_text = models.TextField(null=True, blank=True)

    # --- 3. 关联与状态 ---
    # 弱关联：具体的 AudioSlice ID (点击查找后绑定)
    slice_id = models.ForeignKey('AudioSlice', null=True, blank=True, on_delete=models.SET_NULL)
    
    # 复习高亮
    HIGHLIGHT_CHOICES = [('none', 'None'), ('yellow', 'Review'), ('red', 'Hard')]
    hili_type = models.CharField(max_length=20, choices=HIGHLIGHT_CHOICES, default='none')

    class Meta:
        ordering = ['chunk_id', 'index']
        indexes = [models.Index(fields=['chunk_id', 'index'])]
```

---

## 3. 后端逻辑 (Backend Logic)

### A. 解析与入库 (Ingestion)

- **目标**：从网页抓取，清洗数据，全部存入 **Target Chunk ID** (该集第1个Chunk)。
    
- **清洗策略**：
    
    - **Scene**: 识别 `[Scene: ...]` -> `type='scene'`
        
    - **Dialogue**: 识别 `Joey: ...`
        
        - 将 `(...)` 内容提取到 `action_note`。
            
        - 剔除括号后的纯文本存入 `text`。
            
    - **Standalone Action**: 无法匹配 Speaker 且包含括号 -> `type='action'`。
    - 中间 `<h3>` tag，并且不包含 [] (Scene) 或者 () （旁白或动作）可以忽略
        
示例剧本：

```Text
### [Scene: Central Perk. Everyone’s sitting on the couch and Phoebe enters.]

**Phoebe**: Hi

**All**: Hey! Hi!

**Rachel**: How was the honeymoon?

### **OPENING CREDITS**

### [Scene: Central Perk. Phoebe’s trying to teach Joey French, so she’s sitting in front of him with the script in her hands.]

**Phoebe**: All right, it seems pretty simple. Your first line is "My name is Claude", so, just repeat after me. "Je m’appelle Claude".

**Joey**: Je de coup Clow.

(Joey takes the plastic container to his mouth and starts to drink. Most of the milk gushes from the bottle down his chin and over his clothes to the floor. He keeps "drinking" and all of a sudden he lifts it up and half the bottle of milk pours out in an instant. He then continues to drink the rest. He then puts the empty container down on the counter.)

**Phoebe**: (checking her watch) You did it !

### End

**_© [Fan Club Français de Friends](http://www.fanfr.com/) & [Friends Generation 2](http://www.friendsgeneration.com/)_**
```
### B. 读取接口 (Fetch API)

- **逻辑**：不需要加载全量数据。
    
- **优化**：`GET /workbench/:id/script` 默认只返回 `index` 最小的前 50 行**。
    
    - _理由_：用户只会操作前几十行来切分，后面的即使加载了也会被切走。
        

### C. 剪切接口 (Split API) - 核心功能

- **Endpoint**: `POST /workbench/:id/split`
    
- **Payload**: `{ "start_index": 21, "next_chunk_id": 14 }`
    
- **SQL 逻辑**:

    
    ```SQL
    UPDATE script_line 
    SET chunk_id = 14 
    WHERE chunk_id = 13 AND index >= 21;
    ```
    
- **Undo 逻辑 (后悔药)**:
    
    - 前端保留本次操作的 Context。
        
    - 如果 Undo，调用反向接口把 chunk_id 改回 13。
        

---

## 4. 前端 UI/UX (Side Panel)

### A. 布局与渲染

- **容器**：右侧独立 Side Panel，单列流式布局。
    
- **渲染样式**：
    
    - **Dialogue**: 气泡样式。`action_note` 显示在气泡下方/旁边的灰色小字 (Subtext)。
        
    - **Action**: 居中、灰色、斜体、无气泡。
        
    - **Scene**: 分割线样式 `—— Central Perk ——`。
        

### B. 交互设计：剪切 (The Split)

- **触发入口**：
    
    - **默认隐形**：鼠标 Hover 到某一行时显示。
        
    - **图标位置**：行最左侧 (Left Sidebar of the row)。
        
    - **图标样式**：`->|` (Next / Push Icon)。
        
    - **Tooltip**: _"Start [Chunk #14] from here"_ (动态显示下一个 Chunk 的名字/ID)。
        
- **点击反馈**：
    
    - **动画**：被切分出去的行（当前行及之后所有）执行 **Slide Down + Fade Out** (向下划出并消失)。
        
    - **数据**：列表瞬间变短，只剩切分点之上的内容。
        
- **后悔药 (Toast)**：
    
    - 底部弹出 Toast: _"Moved 450 lines to Chunk #14. [Undo]"_。
        
    - 点击 Undo 立即恢复。
        

### C. 交互设计：查找与定位 (Search & Anchor)

- **触发**：Hover 行右侧显示 `🔍`。
    
- **逻辑**：
    
    - 点击 `🔍` -> 在左侧 Audio Slices 中搜索匹配文本。
        
    - **命中**：左侧滚动到对应卡片 + 卡片闪烁高亮 + 自动保存 `slice_id` 到该行。
        
    - **未命中**：Toast 提示 "No audio found"。
        
- **已连接状态**：如果该行已有 `slice_id`，显示微弱的绿色信号图标 `((·))` 或文字加深。
    

---

## 5. 开发路线图 (Dev Checklist)

1. **Model Migration**: 创建/更新 `ScriptLine` 表结构。
    
2. **Parser Script**: 编写 Python 脚本，跑通 `fanfr.com` 的抓取，将 S10E13 存入 Chunk #13 (假设)。
    
3. **API Dev**: 写好 `list` (limit 100) 和 `split` (update) 两个接口。
    
4. **Frontend List**: 渲染右侧基础列表 (区分三种类型样式)。
    
5. **Frontend Split**: 实现 Hover 图标、点击 API 调用、以及最重要的 **消失动画** 和 **Undo Toast**。
    
6. **Integration**: 联调，享受丝滑的“推入”体验。