# %%
from pydoc import text
from dataclasses import dataclass
@dataclass
class Person:
    name: str
# %%
edith = Person(name="edith")
# %%
edith.__dict__
# %%
class SlotPerson:
    __slots__ = ['name']  # 提前挖好坑，只能放 name

p2 = SlotPerson()
p2.name = "Edith"

# ❌ 报错！因为它没有 __dict__ 了，内存更紧凑
try:
    print(p2.__dict__)
except AttributeError as e:
    print("报错啦:", e)
# 输出: 报错啦: 'SlotPerson' object has no attribute '__dict__'
# %%
import sys

# 1. 普通类 (使用 __dict__)
class Normal:
    def __init__(self):
        self.x = 1
        self.y = 2

# 2. Slots 类 (固定内存)
class Slotted:
    __slots__ = ['x', 'y']
    def __init__(self):
        self.x = 1
        self.y = 2

# 实例化
obj_normal = Normal()
obj_slotted = Slotted()

# --- 见证真相 ---

# 普通对象本身大小 + 它的 __dict__ 大小
size_normal = sys.getsizeof(obj_normal) + sys.getsizeof(obj_normal.__dict__)

# Slots 对象大小 (它没有 __dict__)
size_slotted = sys.getsizeof(obj_slotted)

print(f"普通对象占用: {size_normal} bytes")
print(f"Slots对象占用: {size_slotted} bytes")

# 典型输出 (Python 3.10+):
# 普通对象占用: 152 bytes  (48 + 104) -> 字典本身就很重
# Slots对象占用: 48 bytes   -> 极其紧凑
# %%
n = 4
n_str = f"{n:02d}"
n_3_str = f"{n:03d}"
print(n_str, n_3_str)
# %%
cleaned = "Mr Zelner: ".strip(':')
print(cleaned)

cleaned_2 = "Mr Zelner: ".strip()
print(cleaned_2)

cleaned_3 = "Mr Zelner:".strip(':')
print(cleaned_3)
# %%
import re

text = "bar foo"
pattern = "foo"

print(re.match(pattern, text))
print(re.search(pattern, text))
# %%
import re

text = "<div>hello</div><div>world</div>"
pattern = r"<div>(.*?)</div>"

matches = re.search(pattern, text)
print(matches)

pattern2 = r"<div>(.*)</div>"

matches2 = re.search(pattern2, text)
print(f"""
{matches2}, 
{matches2.group(0)}, 
{matches2.group(1)}
""")
# %%
text = "abbbnana"
print(text.strip("a"))
# %%
print('www.example.com'.strip('cmowz.'))
# %%
