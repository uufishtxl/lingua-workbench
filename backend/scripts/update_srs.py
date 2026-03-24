import re
from datetime import datetime
import codecs

filepath = r'c:\projects\my-tech-notebook\50-Quiz\03-06\03-06-QUIZ.md'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

replacements = {
    'Q1': '> 💡 **解析**：❌ **(答错 - 顺位有误)**\n> \n> `get_object()` 的核心动作顺序极其重要：\n> 1. 先执行 `get_object_or_404(queryset, **filter_kwargs)` 从数据库获取对象。**如果找不到，直接抛出 404，后续代码不执行**。\n> 2. 获取到对象后，才执行 `self.check_object_permissions(self.request, obj)`。\n> 3. 如果没权限，抛出 **403 Forbidden**（未登录则 401）。\n> **核心防御价值**：这样的顺序是为了**避免泄露数据存在性**。如果先校验权限且报错 403，意味着攻击者能探测出这个 ID 在数据库里存在。先报 404 就可以隐藏它的存在。(打回 Box 1)\n',

    'Q2': '> 💡 **解析**：✅ **(完全正确)**\n> \n> 补充：DRF 中的全局分页影响很大。你提到的 `pagination_class = None` 是一种干净利落的”局部退化“策略，可以确保该 ViewSet 的 list 结果永远是一个干净的 Array，这在需要拉取下拉列表全部选项时特别有用。\n',

    'Q3': '> 💡 **解析**：✅ **(完全正确)**\n> \n> 总结得很棒！核心判断依据就是“幂等性”。多次执行是否产生不同影响。POST/PATCH 确实不具备天然的幂等性。\n> 补充 RPC 和 批量操作选用 POST，说明你吃透了这个知识点。\n',

    'Q4': '> 💡 **解析**：✅ **(完全正确)**\n> \n> 注意你提到的 `filter`：任何非 `none` 的 `transform`、`filter` 或者 `opacity` 不为 1 都会使得浏览器为该元素创建一个**新的层叠上下文（Stacking Context）**，从而把它的子元素困在里面，导致 z-index 无法与外部竞级。`Teleport` 拔出了这把锁！\n',

    'Q5': '> 💡 **解析**：✅ **(完全正确)**\n> \n> 没错！Audio 对象只有在 `readyState >= 1` (HAVE_METADATA) 时，它的 `duration` 和各种媒体属性才被载入。在此之前强制设置 `currentTime` 会引发 InvalidStateError 报错。\n',

    'Q6': '> 💡 **解析**：✅ **(完全正确)**\n> \n> 幻觉往往来自于大模型根据自己预训练的数据进行“脑补”。显式路径不仅是“告诉它去哪里找”，更是利用物理约束掐断了它的发散余地。\n',

    'Q7': '> 💡 **解析**：✅ **(完全正确)**\n> \n> 完美的语法。利用 `<script setup generic="T">` 可以解决以前 Options API 中难以向组件内部声明类型变量的痛点。\n',

    'Q8': '> 💡 **解析**：✅ **(完全正确)**\n> \n> DOM 级事件（尤其是 document, window, body 上挂载的事件）并不跟随 Vue 组件的生命周期被清理，这不仅导致内存泄露，还会带来极其难缠的“幽灵触发（Ghost Triggering）”现象。必须在 `onUnmounted` 一一对应地 `remove`。\n',

    'Q9': '> 💡 **解析**：✅ **(优秀！)**\n> \n> 你的分析证明了你很清楚框架的内在规则。不过，在**工业级**架构中，我们依然提倡：**就算是隐式 read_only，最好也再写一遍到 `read_only_fields` 里面去。**\n> 为什么？因为这叫做“Defense in Depth（纵深防御）”和“Contract Explicitness（契约显式化）”。你在 Serializer 层面显式声明，那么即使未来某个队友在 Model 层面手欠改掉了 `auto_now_add`，这个字段在这个 API 里依然受到只读保护。这也方便 Code Review 时一眼看出哪些字段受到保护。\n',

    'Q10': '> 💡 **解析**：✅ **(深度思考！)**\n> \n> 你把两者的优劣都分析透了！\n> - **`@action(detail=True)` 归属 DramaViewSet**: 路由很漂亮 (`/dramas/1/seasons/`)，也是经典的嵌套资源形式。缺点需要重写 `get_serializer_class` 或引入强耦合，遇到复杂查询、分页容易变成屎山。\n> - **归属 SeasonViewSet (`GET /seasons/?drama_id=1`)**: 将资源平行化处理，只需要简单的 `django-filter` 就能利用原生 ViewSet 强大的 `ListModelMixin` 完成搜索过滤。这是**API First** 架构更提倡的弱耦合模型。\n> \n> 二者取舍见功力。你的理解非常到位！\n'
}

for q, answer_feedback in replacements.items():
    # Only replace if not already replaced
    if "💡 **解析**" not in content.split(f'### {q}.')[1].split('###')[0]:
        pattern = rf'(### {q}\..*?\*\*答案\*\*:.*?)(?=\n\n(?:###|##)|$)'
        def repl(m):
            return m.group(1) + '\n\n' + answer_feedback
        content = re.sub(pattern, repl, content, flags=re.DOTALL)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

# Next, update srs_tracker.md
srs_path = r'c:\projects\my-tech-notebook\review\srs_tracker.md'
with open(srs_path, 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

today_str = datetime.now().strftime('%Y-%m-%d')

outcomes = {
    '[DRF/ViewSet] get_object() 内幕': 'stay', # wrong
    '[Django/DRF] ViewSet 隐式分页陷阱 (pagination_class = None)': 'next',
    '[API Design] POST/PUT/PATCH 甄别与打破语义迷信 (幂等性判断)': 'next',
    '[Vue/Animation] 过渡与 z-index 叠放陷阱 (Teleport & Popper 解决层叠上下文隔离)': 'next',
    '[Frontend/Audio] HTML5 Audio 的就绪判定与 InvalidStateError 防御 (readyState >= 1)': 'next',
    '[Prompt Engineering] 针对工具调用的显式路径引导 (Explicit Path Guidance)': 'next',
    '[Vue] Script Setup Generics (generic="T")': 'next',
    '[Vue/Events] Global Event Lifecycle (内存泄漏与幽灵触发)': 'next',
}

box_map = {
    '## Box 1 (Daily)\n': 1,
    '## Box 2 (Every 3 Days)\n': 2,
    '## Box 3 (Weekly)\n': 3,
    '## Box 4 (Bi-weekly)\n': 4,
    '## Box 5 (Mastered)\n': 5,
}

current_box = 0
items_by_box = {1: [], 2: [], 3: [], 4: [], 5: []}
other_lines = []

for idx, line in enumerate(lines):
    if line in box_map:
        current_box = box_map[line]
        continue
    
    if current_box == 0:
        other_lines.append(line)
        continue
        
    if line.strip().startswith('- [ ]'):
        match_found = False
        for k, action in outcomes.items():
            if k in line:
                line = re.sub(r'\(Last: \d{4}-\d{2}-\d{2}\)', f'(Last: {today_str})', line)
                
                # IMPORTANT: Replace '[ ]' with '[x]' for correct items if that is standard, but the instructions say move to next box, so checking them off may help visually
                if action == 'stay':
                    items_by_box[1].append(line)
                elif action == 'next':
                    next_box = min(5, current_box + 1)
                    # For SRS, usually it stays as [ ] so it can be answered again in the future
                    items_by_box[next_box].append(line)
                
                match_found = True
                break
        
        if not match_found:
            items_by_box[current_box].append(line)
    else:
        items_by_box[current_box].append(line)

# Add new knowledge
items_by_box[1].append(f'- [ ] [DRF/Serializer] Read-only 字段的显式与隐式声明考量 (Last: {today_str})\n')
items_by_box[1].append(f'- [ ] [API Architecture] 嵌套路由归属权 (Action vs Filter) (Last: {today_str})\n')

# Rebuild the file
with open(srs_path, 'w', encoding='utf-8') as f:
    for line in other_lines:
        f.write(line)
    
    for b in range(1, 6):
        box_header = list(box_map.keys())[b-1]
        f.write(box_header)
        for item in items_by_box[b]:
            f.write(item)

print("SRS tracker updated.")
