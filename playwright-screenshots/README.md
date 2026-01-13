# Playwright 自动化截图工具

为 Lingua Workbench 前端自动截取 SliceCard 组件的多阶段截图。

## 准备事项

### 1. 安装依赖

```bash
cd playwright-screenshots
npm install
npx playwright install chromium
```

### 2. 配置认证 Token

创建 `auth.config.json`（已在 .gitignore 中，不会上传到 Git）：

```json
{
    "accessToken": "你的token",
    "userEmail": "your-email@example.com"
}
```

**获取 Token 的方法**：
1. 在浏览器中登录前端 `http://localhost:5173`
2. 打开 DevTools（F12）→ Console
3. 运行以下代码：
   ```javascript
   JSON.parse(localStorage.getItem("auth")).accessToken
   ```
4. 复制输出的 token 粘贴到 `auth.config.json`

> ⚠️ Token 有效期约 24 小时，过期后需重新获取

### 3. 准备测试数据

在运行截图前，确保：

1. **前端服务运行中**：`http://localhost:5173`
2. **有一个可用的 AudioChunk ID**，并且该 chunk 下有一个**已保存的空白 AudioSlice**
   - 在 Audio Slicer 中选择一段音频区域
   - 点击 "Save All Changes" 保存
3. **记住 chunk ID**（URL 中的数字，如 `/slicer/workbench/15` 中的 `15`）

---

## 配置项

编辑 `src/screenshot.ts` 中的 `CONFIG` 对象：

```typescript
const CONFIG = {
    baseURL: 'http://localhost:5173',    // 前端地址
    workbenchId: 15,                      // ← 修改为你的 chunk ID
    outputDir: path.resolve(__dirname, '../screenshots'),
    transcriptionTimeout: 60000,          // 转录等待时间（毫秒）
    deviceScaleFactor: 2,                 // 截图缩放（2 = 200% 高清）
    textToSelect: 'selling this house',   // ← 修改为要高亮的文本
};
```

| 配置项 | 说明 |
|--------|------|
| `workbenchId` | AudioChunk 的 ID（URL 中 `/slicer/workbench/{id}`） |
| `textToSelect` | Stage 4 要选中的文本（用于演示高亮功能） |
| `deviceScaleFactor` | 截图分辨率倍数，建议与显示器缩放一致 |

---

## 运行截图

```bash
# 无头模式（默认）
npm run screenshot

# 调试模式（显示浏览器窗口）
npm run screenshot:debug
```

---

## 输出文件

截图保存在 `screenshots/{日期时间}/` 目录：

| 阶段 | 文件名 | 说明 |
|------|--------|------|
| 1 | `fig_lwb_audio-slicer_slice-audio.png` | SliceCard 初始状态（波形） |
| 2 | `fig_lwb_audio-slicer_transcribe-text.png` | 转录完成后（有文本） |
| 3 | `fig_lwb_audio-slicer_edit-transcription.png` | 编辑模式 |
| 4 | `fig_lwb_audio-slicer_highlight-text-01.png` | 选中指定文本 |
| 5 | `fig_lwb_audio-slicer_highlight-text-02.png` | 高亮完成 |
| 6 | `fig_lwb_audio-slicer_ai-sound-result.png` | AI 发音分析结果 |
| 7 | `fig_lwb_audio-slicer_edit-sound-display.png` | 编辑 Sound Display |
| 8 | `fig_lwb_audio-slicer_ai-definition-result.png` | AI 词义解释结果 |
| 9 | `fig_lwb_audio-slicer_complete-editing.png` | 退出编辑器完成编辑 |

---

## Playwright 关键知识点

> 💡 不需要背 API，理解概念即可，让 AI 生成代码

### 1. 等待机制

| 方法 | 用途 | 何时使用 |
|------|------|----------|
| `waitForTimeout(ms)` | 固定等待 | ⚠️ 尽量避免，仅用于调试 |
| `waitForSelector(sel)` | 等待元素出现 | 页面加载时等待某元素渲染 |
| `waitForFunction(fn)` | 等待条件满足 | 等待文本变化、状态改变等 |
| `waitForLoadState('networkidle')` | 等待网络空闲 | 等待 API 请求完成 |

```typescript
// ❌ 傻等
await page.waitForTimeout(30000);

// ✅ 智能等待元素
await page.waitForSelector('.my-element');

// ✅ 智能等待条件
await page.waitForFunction(() => {
    return document.querySelector('.text')?.textContent?.length > 5;
});
```

### 2. 查找元素 (Locator)

`Locator` 是**惰性引用**，不是元素本身。每次操作时才查询 DOM。

```typescript
// CSS 选择器
page.locator('.my-class')
page.locator('#my-id')
page.locator('button')

// 包含子元素（:has）
page.locator('button:has(svg)')          // 包含 svg 的 button
page.locator('.card:has(.active)')       // 包含 .active 的 .card

// 链式定位
sliceCard.locator('.text-area')          // 在 sliceCard 内部查找

// 索引选择
page.locator('.item').first()            // 第一个
page.locator('.item').nth(2)             // 第三个（0-indexed）
page.locator('.item').last()             // 最后一个

// 文本选择器
page.locator('text=Submit')              // 包含文本
page.locator('text="Submit"')            // 精确匹配文本
```

### 3. 点击操作

```typescript
// 普通点击（自动等待可点击）
await btn.click();

// 强制点击（绕过遮挡检查）
await btn.click({ force: true });

// 双击
await btn.dblclick();

// 右键
await btn.click({ button: 'right' });
```

### 4. 输入操作

```typescript
// 填充（清空后输入）
await input.fill('hello');

// 逐字输入（模拟打字）
await input.type('hello', { delay: 100 });

// 清空
await input.clear();
```

### 5. 常见问题

| 错误信息 | 原因 | 解决方案 |
|----------|------|----------|
| `element intercepts pointer events` | 元素被遮挡 | 加 `{ force: true }` |
| `waiting for selector timeout` | 元素不存在 | 检查选择器是否正确 |
| `element is not visible` | 元素隐藏 | 先滚动到可见区域 |

---

## 参考资料

- [Playwright 官方文档](https://playwright.dev/docs/intro)
- [Locator 选择器文档](https://playwright.dev/docs/locators)

