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