# Pomodoro Standalone App 开发全流程指南

针对番茄钟应用从 `reader` 剥离为独立 `standalone app` 的实战大纲。

---

## 第一阶段：骨架搭建 (Models)
**重点：定义出数据结构和“状态”**
1.  **用户关联**：别忘了每个专注记录都应该属于一个 `User` (ForeignKey)。
2.  **标签系统 (`PomodoroTag`)**：
    - `name` (CharField)
    - `order` (IntegerField) - 用于前端排序。
3.  **核心记录 (`Pomodoro`)**：
    - `user`, `tag` (ForeignKey)。
    - `duration` (IntegerField) - 专注时长。
    - `status` (CharField) - **核心实战点**：使用 `choices` 定义有限状态机（如：`STARTED`, `COMPLETED`, `INTERRUPTED`）。
    - `created_at` (auto_now_add)。
    - `completed_at` (DateTimeField, null=True) - **修正逻辑**：不要用 `auto_now_add`，这个时间应该在任务真正结束时通过 API 手动填入。

## 第二阶段：契约定义 (Serializers)
**重点：处理嵌套和只读安全**
1.  **`PomodoroTagSerializer`**：简单的字段定义。
2.  **`PomodoroSerializer`**：
    - **嵌套展示**：把 `tag` 嵌套进来显示名字，而不是只给一个 ID。
    - **安全保护**：把 `id`, `created_at`, `completed_at`, `status` 设为 `read_only_fields`。这些神圣的时间戳和状态不应该允许前端通过 POST 乱改。

## 第三阶段：门户开放 (Views & URLs)
**重点：利用 ViewSet 的高效率**
1.  **`ModelViewSet`**：利用 `viewsets.ModelViewSet` 快速搞定 CRUD。
2.  **权限控制**：确保 `permission_classes = [IsAuthenticated]` 且 `get_queryset` 只能查到当前用户的数据。
3.  **动作定义 (Custom Actions)**：
    - **实战点**：在 `PomodoroViewSet` 里写一个 `@action(detail=True, methods=['post'])` 的 `finish` 方法。
    - **逻辑**：当前端调用这个接口时，后端自动设置 `status='completed'` 并更新 `completed_at=timezone.now()`。
4.  **路由注册**：在 `pomodoro/urls.py` 里用 `SimpleRouter` 注册，并挂载到主项目的 `api_v1_urls.py`。

## 第四阶段：后勤保障 (Admin)
**重点：监控与校验**
1.  **可视化**：配置 `list_display` 让你在后台一眼看到哪些计时正在进行。
2.  **只读显示**：利用 `readonly_fields` 让自动生成的时间戳可见。

---

## 💡 开发者锦囊
- **先写模型，先跑迁移**：稳住底座。
- **手动补全 ViewSet**：在 `create` 方法里自动给 `user` 赋值。
- **感受状态机**：打通“创建 -> finish -> 观察时间”的完整链路。
