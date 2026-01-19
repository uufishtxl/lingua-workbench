# Lingua Workbench TODO

## 代码改进

### 🔴 统一错误处理
目前各处 catch 块各自处理，建议：
- 创建 `errorHandler` 工具类
- 统一错误日志格式
- 统一用户提示（ElMessage）

### 🟡 类型安全增强
- [ ] `setSliceCardRef` 的 `el` 参数使用 `any`，改为明确类型
- [ ] 检查其他 `:ref` 回调的类型

### ✅ SliceCard 重构
SliceCard.vue 已重构完成：
- [x] 按照标准顺序重排代码：imports → props/emits → refs → computed → composables → methods → watch → lifecycle
- [x] 提取 `useHighlightSelection` composable - 文本选择 + 高亮图标逻辑
- [ ] 提取 `useSliceData` composable - 数据收集 + expose 方法 (暂不实施)

---

*Created: 2026-01-16*
