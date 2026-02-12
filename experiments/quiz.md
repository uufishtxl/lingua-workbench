# 📝 今日复习 (2026-02-06)

## 🔧 后端 (Backend) - 5 题

### Q1. [错题复习] Django `update()` 与 signals
```python
User.objects.filter(is_active=False).update(is_active=True)
```
这个操作会触发 `post_save` signal 吗？为什么？

### Q2. [新题] Django Management Command
在 Django 中创建自定义命令 `python manage.py my_task`，需要满足哪些条件？（至少说 3 点）

### Q3. [新题] argparse `action='store_true'`
```python
parser.add_argument('--verbose', action='store_true')
```
当用户运行 `python manage.py my_task` 时（不带 `--verbose`），`options['verbose']` 的值是什么？

### Q4. [错题复习] Django `makemigrations` Non-null 问题
给一个已有数据的 model 添加一个 `CharField(max_length=100)` 字段（不设默认值），运行 `makemigrations` 会发生什么？有哪两种解决方案？

### Q5. [错题复习] `multipart/form-data` 用在什么场景？
在 HTTP 请求中，`Content-Type: multipart/form-data` 通常用于什么类型的请求？为什么不能用 `application/json`？

## 🐍 Python 基础 - 5 题

### Q6. [错题复习] `strip()` 的行为
```python
s = "  hello world  "
print(s.strip())
```
输出什么？如果 `s = "xxhelloxx"`，`s.strip('x')` 输出什么？

### Q7. [错题复习] `raise_for_status()`
```python
import requests
response = requests.get("https://example.com/404")
response.raise_for_status()
```
如果服务器返回 404，这段代码会怎样？不调用 `raise_for_status()` 会怎样？

### Q8. [错题复习] 正则表达式 Greedy vs Non-greedy
```python
import re
text = "<div>hello</div><div>world</div>"
print(re.findall(r"<div>.*</div>", text))
print(re.findall(r"<div>.*?</div>", text))
```
分别输出什么？解释 `*` 和 `*?` 的区别。

### Q9. [错题复习] `re.match()` vs `re.search()`
```python
import re
text = "hello world"
print(re.match(r"world", text))
print(re.search(r"world", text))
```
分别输出什么？为什么？

### Q10. [新题] `Path` 操作
```python
from pathlib import Path
p = Path("/home/user/docs/file.txt")
```
写出获取以下内容的代码：
- 文件名（含扩展名）
- 文件名（不含扩展名）
- 扩展名
- 父目录

## 🎨 前端 (Frontend) - 5 题

### Q11. [错题复习] CSS `z-index` 失效
```css
.box {
  z-index: 999;
}
```
为什么有时候设了超大的 `z-index` 却没有效果？需要满足什么前提条件？

### Q12. [错题复习] Vue `key` 的作用
在 `v-for` 中为什么要绑定 `:key`？如果不绑定或者用 `index` 作为 key 会有什么问题？

### Q13. [新题] Vue 生命周期
```javascript
onMounted(() => {
  console.log('mounted')
})
onBeforeMount(() => {
  console.log('before mount')
})
```
这两个 log 的打印顺序是什么？`onMounted` 时能访问 DOM 吗？

### Q14. [新题] TypeScript `Partial<T>`
```typescript
interface User {
  id: number;
  name: string;
  email: string;
}
```
如何用内置工具类型创建一个"所有字段都可选"的 `User` 类型？

### Q15. [新题] HTTP 状态码
说出以下状态码的含义：
- 200
- 201
- 400
- 401
- 404
- 500