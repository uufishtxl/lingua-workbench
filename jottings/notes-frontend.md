# 前端学习笔记

## 📌 知识点速查

| 知识点 | 一句话解释 |
|--------|-----------|
| **Blob** | 浏览器中表示二进制数据的对象，用于文件处理（图片、音频、视频等） |
| **Fetch vs Axios** | Axios 是 Fetch 的封装，自动处理 JSON 解析、错误抛出、查询参数拼接；查询参数本质都是字符串 |
| **Axios 泛型** | `axios.post<T>()` 的泛型 T 指定的是 `response.data` 的类型，而非整个 response |
| **Vite Proxy vs CORS** | Vite Proxy 仅在开发环境绕过跨域，生产环境必须依赖后端 CORS 配置 |
| **Fetch Response 读取** | `.json()` / `.text()` / `.arrayBuffer()` / `.blob()` 根据数据类型选择，只能读一次 |
| **FormData** | 键值对集合，用于构建表单数据上传；`append(key, value, filename)` 添加字段 |
| **音频截取** | Web Audio API：下载 → 解码 AudioBuffer → 按时间截取 → 编码 WAV Blob |
| **解构默认值** | `const { a = 1 } = obj` 当 `obj.a` 为 `undefined` 时使用默认值 |
| **Promise 轮询** | 循环中 `await sleep()` 等待，根据状态 `return`(fulfilled) 或 `throw`(rejected) |
| **Vue watch immediate** | `{ immediate: true }` 让 watch 在初始化时立即执行一次，而非等值变化 |
| **HTML title 属性** | 原生 HTML 属性，所有元素都支持，显示浏览器原生 tooltip |
| **el-button text** | Element Plus 按钮属性，移除背景和边框，只保留文字/图标 |
| **Tailwind 小数间距** | v3+ 支持 `gap-1.5`(6px)、`gap-0.5`(2px) 等，无需 `gap-[6px]` |
| **flex-1 vs shrink-0** | `flex-1` 占满剩余空间，`shrink-0` 禁止收缩保持原尺寸 |
| **Vue .prevent 修饰符** | `@keydown.enter.prevent` 阻止默认行为（如 enter 换行） |
| **Composable** | Vue 3 可复用逻辑函数，封装 ref/computed/方法，生命周期与调用组件绑定 |
| **Map vs Object** | Map 支持任意键类型、保证顺序、频繁增删更快；动态 key 场景用 Map |
| **Tailwind group** | 父子联动：父元素加 `group`，子元素用 `group-hover:` 实现悬停时显示 |
| **闭包 (Closure)** | 函数 + 它记住的外部变量；让函数能访问创建时的上下文 |
| **Vue 事件闭包模式** | `@event="(val) => handler(id, val)"` — 闭包捕获 v-for 的 id，子组件只传值 |

---

## 1. Fetch vs Axios

> **一句话**：Axios 是对 Fetch 的封装，更易用。

### 对比

| 特性 | Axios | Fetch |
|------|-------|-------|
| 查询参数 | `params: {}` 自动处理 | 需手动拼接 URL |
| 响应数据 | `response.data` 直接拿 | 需 `await response.json()` |
| 错误处理 | 4xx/5xx 自动抛异常 | 需检查 `response.ok` |
| 请求取消 | 内置 CancelToken | 需 AbortController |

### 示例对比

```typescript
// Axios
const response = await axios.post('/api/upload', formData, {
    params: { skip_llm: 'true' }
});
const data = response.data;

// Fetch
const response = await fetch('/api/upload?skip_llm=true', {
    method: 'POST',
    body: formData,
});
if (!response.ok) throw new Error(response.statusText);
const data = await response.json();
```

### Axios 泛型指定响应类型

```typescript
// 泛型 <T> 指定的是 response.data 的类型，不是整个 response！
const response = await axios.post<TranscribeResponse>(url, data);

response        // 类型: AxiosResponse<TranscribeResponse>
response.data   // 类型: TranscribeResponse ← 泛型指定的是这里
```

**原理**：Axios 内部定义了 `AxiosResponse<T>` 类型：
```typescript
interface AxiosResponse<T = any> {
    data: T;           // ← 泛型参数用在这里
    status: number;
    headers: ...;
}
```

---

## 2. Vite Proxy vs CORS

> **一句话**：前端 `vite.config.ts` 的代理设置是为了将 API 请求转发到其他服务。**只在开发环境有用**，生产环境需要后端 CORS。

```
浏览器 → Vite (5173) → 后端 (8000/8001)
         ↑ 同源         ↑ 代理转发
```

| 场景 | 解决方案 |
|------|---------|
| 开发 | Vite Proxy |
| 生产 | 后端 CORS |

---

## 3. Fetch Response 读取

> **一句话**：`fetch` 返回的 Response 有多种读取方法，根据数据类型选择。

```typescript
await response.json()        // → Object (API)
await response.text()        // → string
await response.arrayBuffer() // → ArrayBuffer (音频/文件)
await response.blob()        // → Blob
```

⚠️ Response body 只能读取**一次**！

---

## 4. Blob

> **一句话**：Blob 是浏览器中表示**二进制数据**的对象，用于文件处理。

```typescript
// 创建
const blob = new Blob([data], { type: 'audio/wav' });

// 转 URL（预览/下载）
const url = URL.createObjectURL(blob);

// 上传
formData.append('file', blob, 'audio.wav');
```

| Blob | ArrayBuffer |
|------|-------------|
| 不可变、带 MIME 类型 | 可操作字节 |

---

## 5. FormData

> **一句话**：FormData 是键值对集合，用于构建表单数据上传。

```typescript
const formData = new FormData();
formData.append('file', blob, 'filename.wav');  // (字段名, 值, 文件名)
formData.append('name', 'test');                // (字段名, 值)
```

**注意**：同一个 key 可以 append 多次（多文件上传）

---

## 6. audioUtils.ts 骨架

> **一句话**：从音频 URL 截取指定时间段，编码为 WAV Blob

```
extractAudioSegment(url, start, end) → Blob

流程：下载 → 解码 → 截取 → 编码 WAV
```

| 概念 | 说明 |
|------|------|
| AudioContext | Web Audio API 核心 |
| AudioBuffer | 解码后的波形数据 |
| sampleRate | 采样率 (44100 = 每秒44100采样) |

---

## 7. 解构赋值 + 默认值

```typescript
const { filename = 'audio.wav', skipLlm = true } = options;

// 等价于
const filename = options.filename ?? 'audio.wav';
const skipLlm = options.skipLlm ?? true;
```

---

## 8. Promise 轮询模式

> **一句话**：`async function` 里，`return` = fulfilled，`throw` = rejected

### 轮询流程

```
查询状态 → completed? → return (fulfilled)
         → failed?    → throw (rejected)  
         → 都不是     → sleep 1秒 → 继续轮询
```

### sleep 函数（重要模式）

```typescript
// 经典写法：让 Promise 等待指定毫秒
await new Promise(resolve => setTimeout(resolve, 1000));

// 封装版
function sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
}
await sleep(1000);
```

**原理**：`setTimeout(resolve, ms)` 直接把 `resolve` 函数传给 `setTimeout`，ms 毫秒后自动调用。

---

## 9. HTML title 属性

> **一句话**：原生 HTML 属性，所有元素都支持，显示浏览器原生小提示框。

```html
<button title="这是提示">按钮</button>
```

⚠️ 与 Element Plus 的 `el-tooltip` 不同，`title` 是原生的、不可自定义样式。

---

## 10. el-button text 属性

> **一句话**：Element Plus 按钮属性，移除背景和边框，只保留文字/图标。

| 属性 | 效果 |
|------|------|
| 无 | 默认按钮（有背景、边框） |
| `text` | 透明背景，只有文字 |
| `link` | 链接样式 |

```vue
<el-button>默认</el-button>
<el-button text>文字按钮</el-button>
```

---

## 11. Tailwind 小数间距

> **一句话**：Tailwind v3+ 支持小数值，无需自定义 `[]` 写法。

| 类名 | 等价 CSS |
|------|----------|
| `gap-0.5` | 2px |
| `gap-1` | 4px |
| `gap-1.5` | 6px |
| `gap-2.5` | 10px |
| `gap-3.5` | 14px |

---

## 12. flex-1 vs shrink-0

> **一句话**：`flex-1` 占满空间，`shrink-0` 禁止收缩。

| 类名 | 等价 CSS | 含义 |
|------|----------|------|
| `flex-1` | `flex: 1 1 0%` | 可伸可缩，占满剩余 |
| `shrink-0` | `flex-shrink: 0` | 禁止收缩，保持原尺寸 |

```html
<div class="flex">
  <div class="shrink-0">LOGO</div>    <!-- 固定宽度 -->
  <div class="flex-1">内容区</div>    <!-- 填满剩余 -->
</div>
```

---

## 13. Vue 事件修饰符

> **一句话**：`.prevent` 阻止默认行为，`.stop` 阻止冒泡。

```vue
<!-- 阻止 Enter 在 textarea 中换行 -->
<el-input @keydown.enter.prevent="save" />

<!-- 常用修饰符 -->
@click.stop      <!-- 阻止冒泡 -->
@click.prevent   <!-- 阻止默认行为 -->
@click.once      <!-- 只触发一次 -->
```

### ⚠️ 修饰符只适用于原生 DOM 事件

```vue
<!-- ✅ 原生事件：修饰符有效 -->
<div @click.stop="handleClick">

<!-- ❌ 自定义事件：修饰符无效 -->
<BaseWaveSurfer @region-clicked.stop="handleRegionClicked" />
```

**原因**：`@region-clicked` 是组件 emit 的自定义事件，它的参数 `e` 只是普通参数，不是 Vue 可以拦截的事件对象。

**解决**：在处理函数中手动调用 `e.stopPropagation()`：

```typescript
const handleRegionClicked = (region: Region, e: MouseEvent) => {
    e.stopPropagation()  // ← 必须手动调用
    // ...
}
```

---

## 14. Vue Composable

> **一句话**：Vue 3 可复用逻辑函数，封装 ref/computed/方法，让组件专注 UI。

### 基本结构

```typescript
export function useSomething(options) {
  // 1. 状态（内部管理）
  const state = ref(...)
  const status = ref<'idle' | 'loading' | 'done'>('idle')
  
  // 2. 方法（操作状态）
  const doSomething = async () => { ... }
  
  // 3. 返回（暴露给组件）
  return { state, status, doSomething }
}
```

### 什么时候该提取 Composable？

| 信号 | 示例 |
|------|------|
| 一组相关的 ref + 操作函数 | `status`, `result`, `handleClick` 总是一起 |
| UI 无关的业务逻辑 | API 调用、数据处理 |
| 可能在其他组件复用 | 字典查询、AI 分析 |
| 组件超过 300 行 | 考虑拆分 |

### 实际例子：useAiAnalysis

```typescript
// composables/useAiAnalysis.ts
export function useAiAnalysis(options) {
  // 状态
  const analysisResult = ref<Result | null>(null)
  const aiStatus = ref<'default' | 'loading' | 'active'>('default')
  
  // 方法
  const handleAiClick = async () => { ... }
  const getTypeClass = (type: string) => { ... }
  
  // 返回
  return { analysisResult, aiStatus, handleAiClick, getTypeClass }
}

// 在组件中使用
const aiAnalysis = useAiAnalysis({ fullContext, focusSegment })
aiAnalysis.handleAiClick()
```

### 生命周期

- **创建**：组件 `setup()` 执行时
- **销毁**：组件卸载时（内部 ref 被垃圾回收）

### vs 全局状态（Pinia）

```typescript
// ❌ 全局单例（多组件共享同一份数据）
const globalRef = ref(0)
export function useX() { return { x: globalRef } }

// ✅ 每个组件独立实例
export function useX() {
  const x = ref(0)  // 每次调用都是新的
  return { x }
}

// 需要全局共享？用 Pinia store
```

---

## 15. Map vs Object

> **一句话**：Map 支持任意键类型、保证顺序，动态 key 场景更适合。

### 对比

| 特性 | `Map<K, V>` | `{ [key: string]: V }` |
|------|-------------|------------------------|
| 键类型 | 任意（对象、数字等） | 只能 string/symbol |
| 键顺序 | 保证插入顺序 | 不保证 |
| 频繁增删 | 更快 | 较慢 |
| 大小 | `.size` | `Object.keys().length` |

### 使用示例

```typescript
const map = new Map<string, Result>();

map.set(id, result);      // 设置
map.get(id);              // 获取
map.delete(id);           // 删除
map.has(id);              // 检查
map.size;                 // 大小

// 遍历
for (const [key, value] of map) { ... }
```

### 适用场景

- 动态增删键值（如高亮 ID → 分析结果）
- 需要保持插入顺序
- 键不是纯字符串

---

## 16. Tailwind group（父子联动）

> **一句话**：父元素加 `group`，子元素用 `group-hover:` 实现悬停父元素时改变子元素样式。

### 基本用法

```html
<div class="group">
  <span class="group-hover:text-red-500">
    Hover parent to make this red
  </span>
</div>
```

### 实际例子

```html
<div class="group">  <!-- 时间戳容器 -->
  <i-tabler-chevron-left 
    class="w-0 opacity-0 group-hover:w-3 group-hover:opacity-100"
  />
  <!-- 默认隐藏，hover 父容器时显示 -->
</div>
```

### 常用变体

| 变体 | 触发条件 |
|------|----------|
| `group-hover:` | 父元素被悬停 |
| `group-focus:` | 父元素获得焦点 |
| `group-active:` | 父元素被点击 |

---

## 17. 闭包 (Closure)

> **一句话**：函数 + 它能"记住"的外部变量 = 闭包。

### 概念

闭包让函数能够访问**创建时**的作用域，即使函数在其他地方执行。

### 基础示例

```javascript
function createCounter() {
  let count = 0  // ← 外部变量
  
  return function() {  // ← 返回的函数"记住"了 count
    count++
    return count
  }
}

const counter = createCounter()
counter()  // 1
counter()  // 2
counter()  // 3  ← 每次调用都能访问那个 count
```

### 为什么叫"闭包"？

函数把外部变量"封闭/包裹"在自己身上，带走了。

```
┌─────────────────────────┐
│  function()             │
│    ┌───────────────┐    │
│    │ count = 0     │ ←  │ 被"包"进来了
│    └───────────────┘    │
└─────────────────────────┘
```

---

## 18. Vue 事件闭包模式

> **一句话**：父组件用闭包捕获 v-for 的上下文，子组件只需 emit 简单数据。

### 问题场景

v-for 渲染多个子组件，子组件触发事件时，父组件需要知道是**哪一个**。

### 两种解决方式

| 方式 | 子组件 emit | 父组件监听 |
|------|-------------|------------|
| **传统方式** | `emit('event', { id, value })` | `@event="handleEvent"` |
| **闭包方式** | `emit('event', value)` | `@event="(val) => handler(id, val)"` |

### 实际代码（项目中的例子）

```vue
<!-- AudioSlicer.vue (父组件) -->
<SliceCard 
  v-for="region in regionsList"
  :key="region.id"
  @toggle-favorite="(val) => handleToggleFavorite(region.id, val)"
  <!--             ↑ 闭包捕获了当前循环的 region.id -->
/>
```

```typescript
// SliceCard.vue (子组件) - 只 emit 值，不需要知道 id
const toggleFavorite = () => {
  isFavorite.value = !isFavorite.value
  emit('toggle-favorite', isFavorite.value)  // ← 只传 true/false
}
```

```typescript
// AudioSlicer.vue (父组件) - 收到 regionId 和 value
const handleToggleFavorite = (regionId: string, isFavorite: boolean) => {
  const region = regionsList.value.find(r => r.id === regionId)
  if (region) region.isFavorite = isFavorite
}
```

### 闭包如何工作

```javascript
// v-for 每次迭代都创建一个新的箭头函数
// 每个箭头函数"记住"了当时的 region.id

// 迭代1: region = { id: 'abc' }
const handler1 = (val) => handleToggleFavorite('abc', val)  // 记住 'abc'

// 迭代2: region = { id: 'xyz' }
const handler2 = (val) => handleToggleFavorite('xyz', val)  // 记住 'xyz'
```

### 优点

- **子组件更纯粹**：只关心自己的状态变化
- **父组件掌控上下文**：知道是哪个元素
- **代码更简洁**：子组件 emit 更少数据

---

## 19. 高频事件处理策略

> **一句话**：拖拽、滚动、resize 等高频事件需要特殊处理，否则可能产生状态不一致。

### 常见高频事件

| 事件 | 触发频率 |
|------|---------|
| `mousemove` / `touchmove` | 每帧（60fps = 16ms） |
| `scroll` | 滚动时持续触发 |
| `resize` | 窗口调整时持续触发 |
| WaveSurfer `region-updated` | 拖拽区域边界时持续触发 |

### 处理策略

| 策略 | 原理 | 适用场景 |
|------|------|---------|
| **防抖 (Debounce)** | 等用户停止操作 N 毫秒后才执行 | 搜索输入、表单验证 |
| **节流 (Throttle)** | 每 N 毫秒最多执行一次 | 滚动加载、实时预览 |
| **全量清理** | 每次都清理所有旧状态再创建新的 | 状态可能不一致的场景 |

### 实际案例：WaveSurfer 区域重叠 Bug

**问题**：拖拽调整 region 边界时，高频触发导致创建多个同 ID 区域，产生视觉重叠。

**原因**：
```typescript
// ❌ find() 只删一个，如果有多个同 ID 区域就漏删了
const region = existingRegions.find(r => r.id === REGION_ID)
if (region) region.remove()
```

**修复**：使用全量清理
```typescript
// ✅ filter() 找所有同 ID 区域，全部删除
const regionsToRemove = existingRegions.filter(r => r.id === REGION_ID)
regionsToRemove.forEach(r => r.remove())
```

### 教训

> 🎯 **高频事件 + 状态创建 = 必须考虑并发/竞态问题**
> 
> 即使你以为"每次只会有一个"，高频触发下可能产生多个。
