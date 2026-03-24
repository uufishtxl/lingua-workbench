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
some_dict = {}

another_dict = {"name": "Edith"}

print(some_dict.update(another_dict))
print(some_dict)

the_other_dict = {"name": "Tang", "age": 30}
print(some_dict.update(the_other_dict))
print(some_dict)

third_other_dict = {"color": "blue"}
print(some_dict | third_other_dict) # 不会原地更新
print(some_dict)
# %%
ml = [1, 2, 3]
for i in reversed(ml):
    print(i)
# %%
prompt = """- SCRIPT_EDIT — if the user wants to insert, edit, modify, fix, or
correct script lines..."""

print(prompt)
# 实际输出结果（句子被硬生生折断了，变成了两行）：
# - SCRIPT_EDIT — if the user wants to insert, edit, modify, fix, or
# correct script lines...
# %%
prompt = """- SCRIPT_EDIT — if the user wants to insert, edit, modify, fix, or \
correct script lines..."""

print(prompt)
# 实际输出结果（完美连成了一整行）：
# - SCRIPT_EDIT — if the user wants to insert, edit, modify, fix, or correct script lines...
# %%
my_list = set()
my_list.add("1")
print(my_list)
my_list.add("2")
print(my_list)
my_list.add("1")
print(my_list)
# %%
# 解包
list1 = [1, 2]
list2 = [3, *list1]
print(list2)
# %%
# hasattrs
dict1 = {"color": "blue"}
print(hasattr(dict1, "color"))
print('color' in dict1)
print(hasattr(dict1, 'color'))
# %%
from dataclasses import dataclass
@dataclass
class Car:
    color: str
    brand: str
    year: int
    

car = Car("red", "Toyota", 2022)
print(car)
print(hasattr(car, 'color'))
# %%
# 索引
my_list = [1, 2, 3]
print(my_list.index(2))

dict_list = [{'age': 1}, {'age': 2}]
print(dict_list.index({'age': 2}))
# print(dict_list.index({'color': 'red'}))
idx: int
try:
    idx = dict_list.index({'color': 'red'})
except ValueError:
    idx = -1
print(idx)
# %%
a = "   ".strip()
print(a)
print(bool(a))
# %%
from dataclasses import dataclass
@dataclass
class BrandCar():
    color: str
    brand: str

my_car = BrandCar("red", "Toyota")
print(getattr(my_car, 'color'))

print(getattr({'color': 'red'}, 'color', None))
# %%
for i in range(0, 100, 20):
    print(i)
# %%
items = list(range(1, 86)) # 假装这是85个段落
chunk_size = 20

for i in range(0, len(items), chunk_size):
    chunk = items[i:i+chunk_size]
    print(f"Batch from {i} to {i+chunk_size}: length {len(chunk)}")

# %%
class MyClass:
    def __init__(self):
        self.public_var = "public"
        self._protected_var = "_public"
        self.__private_var = "__public"

obj = MyClass()
print(obj.public_var)
print(obj._protected_var)
# print(obj.__protected_var)
print(obj._MyClass__private_var)
# %%
from dataclasses import dataclass
@dataclass(frozen=True)
class Person:
    name: str
    age: int

    def __str__(self):
        return f"{self.name} is {self.age} years old."


person = Person("Edith", 30)
kato = Person("Edith", 30)
bla = Person("Bla", 20)
print(person, person.__hash__, kato.__hash__)
someset = set()
someset.add(person)
someset.add(kato)
someset.add(bla)
print(someset)
# person.name = "edith"

class MutablePerson:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def __hash__(self):
        return hash((self.name, self.age))

    def __eq__(self, other):
        return self.name == other.name and self.age == other.age

    def __str__(self):
        return f"{self.name} is {self.age} years old."

mp = MutablePerson("Edith", 30)
print(mp)
mp.age = 20
print(mp)

# %%
somedict = {'id': 1, 'color': 'red'}
items = somedict.items()
print(items, type(items))
for key, value in items:
    print(key, value)
# %%
for value in somedict.values():
    print(value)
# %%
for key in somedict.keys():
    print(key)
# %%
_new = {key: value for key, value in items}
print(_new)
# %%
