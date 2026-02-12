## 新功能

哦 我还有一个proposal 明天做，就是将A区做成 跑马灯图片，另外一个view 是一个和github类似的网格图，来表示最近1个月/2个月之类的，复习的数据，并且可以让AI根据周期、复习频率、每一个chunk的标黄/红个数来推荐复习哪一个，你觉得可以吗

Thought for 3s


这个想法很棒！让我帮你整理一下这个 proposal：

🎠 Dashboard V2 新功能提案
1. Hero 区跑马灯 (Carousel)
显示多个剧集/Episode 的封面
左右滑动切换
每个卡片点击进入对应的 review 模式
可显示每个剧集的完成进度
2. GitHub 热力图 (Activity Grid)
类似 GitHub Contribution Graph
显示过去 1-2 个月的复习记录
每天一个格子，颜色深浅表示复习量
可以看到自己的学习连续性
3. AI 智能推荐
考虑因素：

时间周期：距离上次复习的天数（遗忘曲线）
复习频率：该 chunk 被复习的总次数
难度标记：chunk 内标黄/标红句子的数量
权重算法：score = days_since_review * 2 + hard_count * 3 + yellow_count * 1
输出：推荐复习的 Top 5 chunks

技术实现思路：

Carousel 用 Swiper.js 或手写 CSS scroll-snap
Activity Grid 自己画（用 CSS Grid）
AI 推荐先用规则引擎，后期可接 LLM
你想让我现在写一个详细的 proposal 文档放到 jottings 里吗？或者明天需要我帮你直接开始做？


---

## 开始Vibe Coding

下一步你想先做哪个？

API /chunks/{id}/complete - 标记 Chunk 完成并返回下一个
API /dashboard/resume - 获取继续学习入口
前端 Dashboard 页面 - 开始做 UI
或者你想先上传一个封面测试一下？

---
🚀 Epic: 交互式学习系统 (Interactive Learning System)
目标：将 Audio Slicer 从一个单纯的“切片编辑工具”升级为一个“具备进度追踪和复习功能的学习平台 (LMS)”。 核心价值：

Dashboard：提供清晰的学习入口，让用户知道“上次学到哪了”。

Visual Index：通过封面图增强记忆和管理的体验。

Flow State：通过“完成并继续”机制，打造无缝的学习心流。

🎨 Part 1: UI 设计规范 (For Pencil / Figma)
请基于以下三个核心界面进行设计。

1.1 首页：学习仪表盘 (Review Dashboard)
这是用户打开 App 后的默认页面。

```
+-----------------------------------------------------------------------+
|  [Logo] Audio Slicer                                      [User Icon] |
+-----------------------------------------------------------------------+
|                                                                       |
|   +---------------------------------------------------------------+   |
|   |                                                               |   |
|   |   [ 背景图：Friends S10E13 封面 (Monica 和 Chandler) ]        |   |
|   |   [ 半透明遮罩层 ...................................... ]     |   |
|   |                                                               |   |
|   |   +-------------------------------------------------------+   |   |
|   |   |  Friends Season 10 Episode 13                         |   |   |
|   |   |  上次进度: Chunk #5 / 24  •  2小时前                  |   |   |
|   |   |                                                       |   |   |
|   |   |  [ ▶ RESUME LEARNING (继续学习) ]                     |   |   |
|   |   +-------------------------------------------------------+   |   |
|   |                                                               |   |
|   +---------------------------------------------------------------+   |
|                                                                       |
|   +---------------------------+    +------------------------------+   |
|   |  📊 难点突击 (Weak Points)|    |  📚 剧集库 (Library)         |   |
|   |                           |    |                              |   |
|   |  🔴 5 Hard (困难)         |    |  1. S10E12 - The Wedding [✅]|   |
|   |  🟡 12 Review (待复习)    |    |  2. S10E13 - French..    [🔄]|   |
|   |                           |    |  3. S10E14 - Goodbye     [🆕]|   |
|   |  [ ⚡ 开始突击复习 ]       |    |                              |   |
|   +---------------------------+    +------------------------------+   |
|                                                                       |
+-----------------------------------------------------------------------+
```

风格可以类似多邻国卡通、明快的样子。

布局：卡片式布局，类似 Netflix 或 Duolingo 首页。

A 区：Hero Card (继续学习) —— 最醒目

背景：当前剧集的封面图（带暗色遮罩）。

内容：

大标题：Friends Season 10 Episode 13

副标题：Last stop: Chunk #5 / 24 (上次停留位置)

时间戳：Last studied: 2 hours ago

Action：一个巨大的 ▶️ 播放按钮，文案 Resume Learning。

B 区：Stats Card (难点突击) —— 次要

视觉：使用红/黄强调色。

内容：12 Sentences to Review (🔴 5 Hard | 🟡 7 Review)。

Action：按钮 Start Weak Point Review。

C 区：Episode Grid (剧集库)

显示所有已导入的 SourceAudio。

状态角标：✅ Completed, 🔄 In Progress.

1.2 组件：智能封面上传 (Smart Cover Uploader)
用于 Dashboard 卡片或编辑页面。

State A (Empty): 灰色虚线框，中心图标 📷，文案 Upload Cover。

State B (Preview): 图片铺满。右下角悬浮绿色按钮 [Save] (带阴影)。

State C (Saved): 图片铺满。鼠标 Hover 时显示右上角半透明 ✏️ Edit 按钮。

交互：支持 Ctrl+V 粘贴图片直接进入 State B。

1.3 页面：Workbench (复习模式状态)
当通过 Dashboard 点击 Resume 进入时：

Side Panel (右侧)：

默认状态：强制展开。

翻译遮挡：中文译文默认显示为模糊/灰色条块，鼠标 Hover 时才清晰显示。

底部栏 (Bottom Bar)：固定悬浮或位于列表最末尾。

主按钮：[Check Circle Icon] Mark Complete & Next (绿色，醒目)。

Audio Player (顶部)：

Loop 模式默认关闭（复习通常是过一遍）。

🛠️ Part 2: Implementation Plan (For Antigravity LLM)
此部分包含详细的数据库变更和 API 逻辑，确保无损迁移。

2.1 数据库设计 (Database Schema)
我们需要修改 SourceAudio 和 AudioChunk 表。所有新增字段均设置为 null=True 或有 default 值，绝对安全，不会影响现有数据。

A. 修改 SourceAudio (增加封面)
Python
# models.py

class SourceAudio(models.Model):
    # ... existing fields (drama, season, etc.) ...
    
    # [NEW] 封面图片
    # 使用 ImageField 需要安装 Pillow 库
    # null=True, blank=True 保证旧数据不出错
    cover_image = models.ImageField(
        upload_to='covers/%Y/%m/', 
        null=True, 
        blank=True,
        help_text="剧集封面/海报"
    )
B. 修改 AudioChunk (增加进度追踪)
Python
# models.py

class AudioChunk(models.Model):
    # ... existing fields ...

    # [NEW] 学习状态标记
    # default=False 保证旧数据默认未学
    is_studied = models.BooleanField(default=False, db_index=True)
    
    # [NEW] 最后学习时间
    # 用于 Dashboard 排序 "Continue Learning"
    last_studied_at = models.DateTimeField(null=True, blank=True)
    
    # [NEW] (Optional) 掌握程度权重，预留给未来算法
    # mastery_score = models.IntegerField(default=0) 
2.2 后端 API 逻辑 (Django View/DRF)
API 1: 获取“继续学习”入口
Endpoint: GET /api/dashboard/resume

Logic:

查询 AudioChunk.objects.filter(is_studied=True).order_by('-last_studied_at').first() 找到上次最后操作的块。

如果找到，查找它的下一个 Chunk (Based on order)。

如果没有学习记录，返回第一个 Chunk。

返回数据结构：{ chunk_id: 15, season: 10, episode: 13, cover_url: "..." }。

API 2: 封面上传
Endpoint: POST /api/audio/:id/upload_cover

Logic: 接收 multipart/form-data 图片，更新 cover_image 字段。

API 3: 标记完成并继续 (Core Flow)
Endpoint: POST /api/chunks/:id/complete

Logic:

更新当前 Chunk: is_studied=True, last_studied_at=timezone.now()。

计算并返回 next_chunk_id。

前端收到响应后，路由跳转至 next_chunk_id。

2.3 前端功能实现 (Vue/React Logic)
A. 状态注入 (Review Mode Injection)
路由监听: 监听 URL Query ?mode=review。

Provide/Inject:

在父组件 (WorkbenchLayout) 解析 URL。

Provide isReviewMode 变量给所有子组件。

B. Side Panel 响应逻辑
JavaScript
// ScriptSidePanel.vue (Pseudo-code)

const isReviewMode = inject('isReviewMode');

// 1. 自动展开
onMounted(() => {
  if (isReviewMode.value) {
    expandPanel();
  }
});

// 2. 完成并继续逻辑
async function handleCompleteAndNext() {
  await api.post(`/chunks/${currentChunkId}/complete`);
  // 跳转到下一个 ID，并保持 review 模式
  router.push({ 
    path: `/workbench/${nextChunkId}`, 
    query: { mode: 'review' } 
  });
}
C. 粘贴上传 (Paste to Upload)
在 EpisodeCover 组件中监听粘贴事件：

JavaScript
function onPaste(event) {
  const items = event.clipboardData.items;
  for (let item of items) {
    if (item.type.indexOf("image") !== -1) {
      const blob = item.getAsFile();
      previewUrl.value = URL.createObjectURL(blob);
      // Show "Save" button
    }
  }
}
🚀 开发顺序建议 (Step-by-Step)
Backend Phase:

执行 makemigrations 和 migrate (Database Update)。

编写 Dashboard 和 Upload 相关的 View/API。

UI Component Phase:

实现 EpisodeCover 组件（先做这个，上传个封面看着爽）。

实现 Dashboard 首页 UI。

Review Logic Phase:

修改 Workbench，增加 isReviewMode 状态处理。

实现 Side Panel 底部的 Complete & Next 按钮及跳转逻辑。