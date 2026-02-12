# 🎯 今日技术复习 (2026-02-05)

## 必考复习题 (来自错题本)
这是昨天的错题，今天优先巩固：

### Q1 [TS] 映射类型语法 (Mapped Types)
以下代码有什么语法错误？如何修正？
```typescript
type ReadonlyUser<T> = {
  key in keyof T: T[key]
}
```

**回答**

```TypeScript
type ReadonlyUser<T> = {
  readonly [key in keyof T]: T[key]
}
```

### Q2 [Pinia] 数据持久化 (Persist)
在 Pinia 中，如果我只想持久化 `token` 字段，而忽略 `isLoading` 字段，`persist` 配置应该怎么写？

**回答**

```TypeScript
return {
    persist: {
        pick: ['token']
    }
}
```

P.S: 我昨天回答对了啊

### Q3 [Vue] Computed 使用
在 `script setup` 中，如何正确打印一个 `computed` 属性的值？
```typescript
const count = ref(1)
const double = computed(() => count.value * 2)
console.log(double) // 这里打印出来是什么？应该怎么改？
```

**回答**
```typescript
const count = ref(1)
const double = computed(() => count.value * 2)
console.log(double.value) // 这里打印出来是什么？应该怎么改？
```

P.S: 我昨天回答对了，这只是换了出题方式
---

## 新题 (Backend - 5道)

### Q4 [Django] 数据库迁移
我们昨天给 `SourceAudio` 加了 `cover_image` 字段，使用了 `null=True`。
如果不加 `null=True` 直接运行 `makemigrations` 会发生什么？Django 会提示你做什么？

**回答**
如果建立过这个 Model 的数据，那么这一步肯定不行。因为既往数据中没有 cover_image 这个字段，这是不被允许的。我不知道会提示什么，但是肯定不会成功。可能需要删表。

<p style="color: red">数据层面的逻辑死局，造成 Django 启动保护机制，会提示用户做出选择：1）手动输入一个值，比如 0，填充给老数据，还是2）退出程序回去改代码加 `default`</p>

### Q5 [Standard] POST vs PATCH
你昨天问到了 `complete` 动作。从语义上讲，`PATCH /api/resource/1/` 和 `POST /api/resource/1/action/` 的主要区别是什么？

**回答**
* `PATCH /api/resource/1/` 会更新指定资源的属性
* `POST /api/resource/1/action/` 会对指定资源执行动作

### Q6 [Python/Regex] 贪婪匹配
我们在修复脚本解析时用了 `*?` (例如 `[A-Za-z\s]*?`)。
正则表达式中 `*` 和 `*?` 的区别是什么？

<p style="color: red">* 是贪婪匹配，*? 是非贪婪匹配</p>

**回答**
* 我记得 + 是一个或多个；? 是 0 个或 1个；忘记对这道题懵了。

### Q7 [Django] ORM update()
昨天我们用 `ScriptLine.objects.filter(...).update(chunk_id=18)` 批量移动了台词。
使用 `update()` 方法会触发模型的 `save()` 方法或 `pre_save/post_save` 信号吗？

**回答**
过

<p style="color: red">不会触发 save() 方法和信号，是 ORM 提供的批量更新方法</p>

### Q8 [API] 文件上传
前端上传图片时，Content-Type 必须设置为什么？Django 后端用什么组件来解析这种请求？

**回答**
image/jpeg 或者 image/png？
用 Pillow，Pillow 可以真的去验证是不是一张图片。

<p style="color: red">multipart/form-data；Django 用 FormParser 解析</p>

---

## 新题 (Python - 5道)

### Q9 [Regex] re.match vs re.search
`re.match('foo', 'bar foo')` 会匹配成功吗？为什么？它和 `re.search` 有什么区别？

**回答**
正则我不行，过

<p style="color: red">不会匹配成功，match() 只从字符串开头匹配，search() 会在整个字符串中查找</p>

### Q10 [String] strip()
`"Mr Zelner: ".strip(':')` 的结果是什么？它是只去除末尾的冒号吗？

**回答**
应该是 Mr Zelner 吧，空格也会去除

<p style="color: red">strip(':') 只去除首尾的冒号。"Mr Zelner: " 结尾是空格，所以冒号去不掉！必须用 strip(': ')。</p>

### Q11 [Python] 类属性 vs 实例属性
```python
class Dog:
    tricks = []
    def add_trick(self, trick):
        self.tricks.append(trick)
```
这样写会有什么潜在 bug？

**回答**
这个 tricks 不是实例的属性啊，用 self.tricks 不对。这是类中的属性。


### Q12 [Requests] 错误处理
我们在 `fetch_script_html` 中调用了 `response.raise_for_status()`。它的作用是什么？如果是 404 会发生什么？

**回答**

过，这里代码我没有看了。

### Q13 [Type Hinting] Optional
`def foo(name: str = None)` 这种写法在类型检查中是严格正确的吗？应该推荐怎么写？

**回答**
不正确，应该是 `def foo(name: str | None = None)`


## 新题 (Frontend - 5道)

### Q14 [CSS] Positioning Context
昨天我们将 Undo Toast 的 `bottom` 改为了 `24`。
`absolute` 定位的元素是相对于哪个父元素定位的？如果不设置 `relative` 会怎样？

**回答**
相对于最近设置了 relative 的父元素。如果不设置，就相对于 body。

### Q15 [CSS] Stacking Context (z-index)
我们给 Undo Toast 加了 `z-10`。
`z-index` 属性在什么情况下才会生效？（即元素的 `position` 必须是什么？）

<p style="color: red">position 不为 static（relative, absolute, fixed, sticky）</p>

### Q16 [Vue] Transition
`<Transition>` 组件只能包含一个根元素吗？如果我有两个元素互斥显示（v-if / v-else），需要加什么属性来确保过渡正常？

也可以是互斥的两个元素，用 mode="out-in" 属性。

### Q17 [Vue] Key 的作用
为什么在 `v-for` 中必须加 `:key`？如果不加或者用 index 作为 key，在列表顺序变化时会导致什么问题？

**回答**

光记住要加 key，但是不知道为什么。如果用 index 作为 key，列表顺序变化时会导致什么问题？

<p style="color: red">Vue 用 key 来追踪每个元素的身份。如果用 index，当列表顺序变化时，Vue 会认为元素的位置变了，而不是内容变了，导致组件复用错误（比如数据错位、动画异常）</p>

### Q18 [TS/Vue] defineProps 类型
在 `script setup` 中，如何为 `defineProps` 定义默认值？

回答：

```TypeScript
const props = withDefaults(defineProps<{
  url: string
  height?: number
  start?: number
  end?: number
  allowSelection?: boolean
}>(), {
  height: 90,
  allowSelection: true,
})
```

---
## 02/04

Q1 [TS] 映射类型语法 ⭐
以下 TypeScript 代码有语法错误，请指出并修正：

```typescript
type MakeOptional<T> = {
  P in keyof T?: T[P]
}
```
**回答**：应该是 `[P in keyof T]?: T[P]`

Q2 [Pinia] 持久化配置 ⭐
你有一个 Pinia store，包含 token（需要持久化）和 tempLoading（不需要持久化）。请写出正确的 persist 配置。

**回答**
```typescript
return {
    persist: {
        pick: ['token']
    }
}
```

Q3 [Vue] computed 返回值 ⭐
以下代码为什么报错？如何修复？

```typescript
const count = ref(0)
const doubled = computed(() => count.value * 2)
// 在 script setup 中
console.log(doubled)  // 输出 [object Object]，不是数字
```
**回答**
不会报错啊，为什么会报错？
箭头函数只有一行，可以省略 `return` 啊
打印 doubled 也没问题啊，如果取值用 .value，不取值没毛病啊


新题 (Backend - 5道)
Q4 [DRF] ViewSet action 装饰器
@action(detail=True) 和 @action(detail=False) 的区别是什么？分别对应什么样的 URL 模式？

**回答**
过

Q5 [Django] 数据库查询优化
以下代码会产生 N+1 问题吗？如何优化？

```python
chunks = AudioChunk.objects.filter(source_audio__user=user)
for chunk in chunks:
    print(chunk.source_audio.drama.name)
```
**回答**
会产生。
```python
chunks = AudioChunk.objects.select_related("source_audio__drama").filter(source_audio__user=user)

for chunk in chunks:
    print(chunk.source_audio.drama.name)
```

Q6 [DRF] Serializer 校验
在 DRF Serializer 中，validate_<field_name> 和 validate 方法的执行顺序是什么？
**回答**
过


Q7 [Django] ImageField 依赖
Django 的 ImageField 需要安装什么额外的库才能正常工作？为什么？

**回答** Pillow 不知道为什么，支持更多格式什么的

Q8 [Backend] REST API 设计
设计一个"标记 chunk 完成"的 API：

用 PUT 还是 POST？为什么？
URL 应该是什么格式？

**回答** 应该用 PUT。因为只更新一个属性？URL 应该是 /api/chunks/{id}/done/

新题 (Python - 5道)
Q9 [Python] 类型注解
Python 3.9+ 推荐使用 list[str] 还是 List[str]？为什么？

list
为什么？不知道，更方便呗，自带的，不需要引入包

Q10 [Python] dataclass
@dataclass(frozen=True) 的作用是什么？它如何影响对象的 hashability？

**回答**
自动生成 __hash__方法，并禁止修改属性。由于不可变，因此可以哈希。

Q11 [Python] with 语句
with open(file) as f: 的底层机制是什么？需要实现哪两个魔术方法？

**回答**
__enter__ 和 __exit__

Q12 [Python] 字典操作
dict.get(key) 和 dict[key] 的区别是什么？什么时候用哪个？

**回答**
dict.get(key) 不存在时，返回 None
dict[key] 如果key 不存在，直接报错

Q13 [Python] f-string 格式化
如何用 f-string 将数字格式化为两位数（如 5 → "05"）？

**回答** 不知道，只会用 zfill

新题 (Frontend - 5道)
Q14 [Vue] watch vs watchEffect
watch 和 watchEffect 的核心区别是什么？各自适合什么场景？

**回答**
watch：显式指定唯一依赖；默认首次不执行；逻辑中可以获取旧值；适合高可控场景；
watchEffect：依赖变化时自动执行；首次执行；逻辑中不可获取旧值；适合 side effect

Q15 [TypeScript] 工具类型
Omit<User, 'password'> 的作用是什么？如何用 Pick 和 Exclude 手动实现它？

**回答**
就是 从 User 中，剔除掉 password 这个属性，生成新的 typing。
我觉得我记住就可以，不想学习如何用 Pick 和 Exclude 手动实现

Q16 [CSS] position 属性
position: sticky 的工作原理是什么？它需要什么条件才能生效？

**回答**
我就知道当浏览器滚动的位置即将脱离这个元素，这个元素就会固定在浏览器的位置。是一个介于 relative 和 fixed 之间的文档流。你的问题我不懂怎么回答。

Q17 [Vue Router] 导航守卫
beforeEach 守卫中的 next() 函数有哪几种调用方式？分别代表什么？

**回答**
next() 继续导航
next{{name: ...}} 跳转到指定路由



Q18 [HTTP] 状态码
201 Created 和 200 OK 什么时候分别使用？RESTful API 中 POST 创建资源成功应该返回哪个？

**回答**
201 是 POST 请求成功
200 OK 是 GET 请求成功
POST 创建资源成功是201啊。
---




## 02/03


## Q1 

有两种方法，一种是通过嵌套 seriazlier（另外还可以 `source`）。


```python
# models.py
from djangos.db import models

class SourceAudio(models.Model):
    title = CharField(max_length=255, blank=True)

class AudioChunk(models.Model):
    source_audio = models.ForeignKey(SourceAudio, on_delete=models.CASCADE)
```

```Python
# serializers.py
from djangos.db import serializers

class SourceAudioSeriazlier(serializers.ModelSeializer):
    class Meta:
        model = SourceAudio
        fields = ['title']

class AudioChunkSerializer(serials.ModelSerializer):
    source_audio = SourceAudioSerializer(read_only=True)
    #...
```

如果是轻型的引用，可以用 source

```python
# serializers.py
class AudioChunkSerializer(serializers.ModelSeializer):
    title = serializers.CharField(source=source_audio.title, read_only=True)
    class Meta:
        model = AudioChunk,
        fields = ['title']
```

## Q2
Read Uncommitted < Read Committed < Repeatable Read < Serializable

## Q3
这种小众的题目别考了吧？DITA 也不会考这个，python更不会考 XML的库。

title 是在当前元素找title 这个 tag
.//title 是在任何下层元素找 title 这个 tag

## Q4
filter 是找到符合条件的；exclude 是剔除符合条件的

## Q5

可以将一个长度很长的唯一的字符串哈希转换为一个32位十六进制字符，这个过程会丢失信息，但是可以用来快速判断两个字符串是否相同。

## Q6
用 __slots__ 可以为类的属性开辟固定的内存分配空间，从而节省内存，但是也意味着不允许动态添加属性。

## Q7
如果数据比较多方法比较少，用 @dataclass；如果方法比较多数据比较少，用普通的 class 进行封装即可

## Q8

同Q3 浪费题目额度

一个是返回元素；一个返回文本

## Q9

这是一个工具类 Class
又一道浪费名额的题目。不需要我在看什么，就考什么题。我只是想了解下之前整个用 DITA 做 RAG 的流程而已。结果你给我出了好几道这种开发和文档面试都不会考的题目。

## Q10
天啊！第四道！
"docs/toic.dita:概述:安装"

## Q11

模板中可以直接使用 $route，这是 Vue Router 提供的全局对象；
但是在 script 中需要通过 composable 引入，也就是 useRoute()

## Q12

作用是只使用 K 中包含的键名，然后结合 P，生成一个新的 typing
```typescript
type Pick<T, K extends keyof T> = {
    [P in K]: T[P]
}
```


## Q13

? 没有问题吧，如果要保留所有属性的状态。除非你要pick 就有问题了

## Q14

什么类型？什么意思？不就是计算属性吗？并且会缓存内存，具有惰性，只有依赖的属性发生变化，才会重新计算，否则可以直接从缓存中读取，比较节约开销。

## Q15

304，表示资源未修改，可以直接从缓存读取。

---

补充：

Q3

比如有一张 author 的表格，也有一张 book 的表格。
当我想要找到素有的 author 的 book 的时候。有两种方法:
* 一种是用 select_related。方法就是将 book 作为主表，然后将 author 的信息 JOIN 到 book 表中。如果用代码表示就是：
```python
books = Book.objects.select_related('author').all
```
* 另一种是用 prefetch_related。
```python
books = Author.objects.prefetch_related('book_set').all()
```

Q8
*args 打包成了 tuple，为了支持位置参数，比如 add(1, 2, 3)
**kwargs 打包成了 dict，为了支持关键值参数，比如 add(a=1, b=2, c=3)

Q9
GET 是幂等的；POST 不是幂等的。
GET 是一种比较安全的操作，不需要查询服务器权限；POST 则需要。
GET 会缓存，POST 不会？

Q10
v-if 会销毁和重建元素，开销比较大；v-show 只是隐藏和显示元素，开销比较小。

---
# 今日题目：

Part 1️⃣ 后端 (Backend) — 5 题
Q1. [Django] Signals
在 Django 中，如果你想在 AudioSlice 模型 保存之后 自动执行一段逻辑（比如更新一个统计字段），应该用哪个 signal？

**回答：B) post_save**

A) pre_save
B) post_save
C) pre_delete
D) post_init

Q2. [DRF] Serializer 嵌套
如果你有一个 SliceSerializer，想在里面嵌套另一个 AudioFileSerializer 来显示其详情（而不是只显示 ID），应该怎么做？请写出字段定义。

**回答：**
不清楚，Vibe Coding多了，这种代码从来没有 hands-on 过。

Q3. [Database] 事务隔离级别
数据库事务的四个隔离级别中，哪个级别最低（并发性最高，但问题也最多）？

A) Read Uncommitted
B) Read Committed
C) Repeatable Read
D) Serializable

**回答：**
D) 不清楚

Q4. [Django] QuerySet 延迟执行
下面代码中，数据库查询真正执行的时机是？
```python
qs = AudioSlice.objects.filter(is_reviewed=True)  # Line A
qs = qs.exclude(translation='')                    # Line B
slices = list(qs)                                  # Line C
```
A) Line A
B) Line B
C) Line C
D) A、B、C 各执行一次

**回答：**
C) Line C


Q5. [API] RESTful 资源命名
按照 RESTful 最佳实践，表示"某个用户的全部订单"的 URL 应该是？

A) /users/123/orders
B) /getOrdersByUser?userId=123
C) /user/123/order/list
D) /orders?user=123 (也可接受，但 A 更 RESTful 嵌套资源)

**回答：**
A) /users/123/orders（直觉和印象上是 A，但是对D也觉得无伤大雅）

Part 2️⃣ Python 基础 — 5 题
Q6. ⭐ [错题] @dataclass frozen=True
请解释：为什么 frozen=True 的 dataclass 可以作为字典的 key？（提示：hash）

**回答：**
因为 `frozen=True` 让 dataclass 的实例不可变，因此可以被 hash。

Q7. ⭐ [错题] 装饰器 timer 实现
你现在打开的文件是 test_decorator.py。请手写一个简单的 timer 装饰器，它能打印被装饰函数的执行时间。需要考虑 @functools.wraps。

**回答：**

```Python
from functools import wraps
import time

def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"函数执行耗费了 {end_time - start_time:.4f} 秒")
        return result
    return wrapper

@timer
def add(a, b):
    time.sleep(1)
    return a + b
```

Q8. ⭐ [错题] list[str] vs List[str]
以下两种写法有何区别？在什么 Python 版本可以用小写？

```python
from typing import List
def foo(items: List[str]) -> None: ...
def bar(items: list[str]) -> None: ...
```

**回答：**
List 需要从 typing 库引入；list 是 Python 内置类型，不需要引入。3.9+ 开始支持 list。

Q9. [Concept] slots
在 Python 类中使用 __slots__ = ['x', 'y'] 的主要目的是什么？

A) 限制实例只能有 x 和 y 两个属性，并节省内存
B) 让属性变成只读
C) 自动生成 __init__ 方法
D) 禁止继承

**回答：**
没有接触过

Q10. [Core] with 语句
with open('file.txt') as f: 语句在退出时会自动调用哪个方法来清理资源？

**回答**

`__exit__`方法

Part 3️⃣ 前端 / 网络 — 5 题
Q11. ⭐ [错题] Vue computed 缓存
请解释 Vue 中 computed 和 methods 的核心区别。为什么官方推荐用 computed 而不是 methods 来做派生计算？

**回答：**
`computed` 本质是一个值，并且带缓存，是惰性的。也就是说，只有当依赖的值发生变化时，才会重新计算。而 `methods` 每次都会重新执行。

Q12. [Vue] watch vs watchEffect
watch 和 watchEffect 有什么区别？什么场景下用 watchEffect 更合适？

**回答：**
`watch`需要显示指定要监听的属性；而`watchEffect`则会自动追踪依赖。因此，如果要同时监听多个属性，`watchEffect`更合适。

Q13. [TypeScript] Pick<T, K>
Pick<T, K> 工具类型的作用是什么？给个例子。

**回答：**
忘记了。

Q14. [CSS] Flexbox Gap
现代 Flexbox 中，如何在子元素之间添加 16px 的间隔？（不用 margin）

**回答：**
设置 `gap` 属性。

Q15. [Network] HTTP Status 304
HTTP 304 状态码代表什么意思？它和浏览器缓存有什么关系？

**回答：**
表示资源未修改，可以直接从缓存读取。
