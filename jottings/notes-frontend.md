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
