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
