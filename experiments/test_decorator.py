# %%
class Student:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def __str__(self):
        return f"{self.name} ({self.age})"

    def __repr__(self):
        return f"Student(name='{self.name}', age={self.age})"

    def __eq__(self, other):
        return (self.name == other.name) and (self.age == other.age)
john = Student("John", 20)
john_2 = Student("John", 20)

print(john)
print(john == john_2)
# %%
from dataclasses import dataclass

@dataclass
class Teacher:
    """A simple class to represent a teacher."""
    name: str
    age: int

mary = Teacher("Mary", 30)
print(mary)

# %%
# __str__ 和 __repr__ 的区别
# __str__ 是用户友好的表示，__repr__ 是开发者友好的表示
# 如果只写了 __repr__，那么 print(john) 也会调用 __repr__
print(john) # 调用 __str__
print([john]) # 调用 __repr__
john # 调用 __repr__

# %% FROZEN
@dataclass(frozen=True)
class ImmutablePoint:
    x: float
    y: float

p = ImmutablePoint(1.0, 2.0)
# p.x = 3.0 # 报错

my_dict = {}
my_dict[p] = "这是一个坐标"
print(my_dict)

# %%
import time
from functools import wraps

def timer(func):
    # 1. @wraps: 别忘了给函数保留“身份证”(元数据)
    @wraps(func)
    def wrapper(*args, **kwargs):
        # 2. 记录开始时间
        start_time = time.time()
        
        # 3. 执行原函数 (一定要接住返回值！)
        result = func(*args, **kwargs)
        
        # 4. 记录结束时间 & 打印
        end_time = time.time()
        print(f"函数 {func.__name__} 执行耗时: {end_time - start_time:.4f} 秒")
        
        # 5. 返回原结果 (千万别忘了这行，否则函数结果就丢了)
        return result
        
    return wrapper

# 用法
@timer
def heavy_process():
    time.sleep(1)
    return "Done"

heavy_process()

# %%
import time
from functools import wraps

def timer(func):
    # 【第一层】这里是工厂，func 就是还没被执行的 add 函数
    @wraps(func)
    def wrapper(*args, **kwargs):
        # --- 步骤 A: 偷窥参数 ---
        # 这里的 args 抓到了 (10, 20)
        print(f"🕵️  [Wrapper] 拦截到了参数: {args}")
        
        # --- 步骤 B: 计时开始 ---
        start_time = time.time()
        
        # --- 步骤 C: 真正的干活 (透传参数) ---
        # 关键！这里相当于执行 add(10, 20)
        # 必须把 catch 到的 result (也就是 30) 拿在手里
        result = func(*args, **kwargs)  
        
        # --- 步骤 D: 计时结束 ---
        end_time = time.time()
        print(f"⏱️  [Wrapper] 耗时: {end_time - start_time:.6f} 秒")
        
        # --- 步骤 E: 交货 (返回值接力) ---
        # 如果这里不 return，外面收到就是 None，程序就崩了
        print(f"🚚 [Wrapper] 准备把结果 {result} 交还给用户")
        return result
        
    return wrapper

# --- 使用装饰器 ---
@timer
def add(a, b):
    print("🤖 [原函数 add] 我正在努力计算 a + b ...")
    time.sleep(0.5) # 假装算得很慢
    return a + b

# --- 见证奇迹的时刻 ---
print("\n--- 开始调用 ---")
final_value = add(10, 20)

print("\n--- 最终结果 ---")
print(f"用户收到的结果: {final_value}")

print(add.__name__)

# %%
class MyRange:
    def __init__(self, limit):
        self.limit = limit
        self.current = 0  # 1. 必须手动维护“当前指针”

    # 2. 握手协议：for 循环开始时会调用它
    def __iter__(self):
        return self 

    # 3. 核心引擎：每一次循环都会调用它
    def __next__(self):
        # 如果还有数据，就返回，并将指针 +1
        if self.current < self.limit:
            val = self.current
            self.current += 1
            return val
        else:
            # 4. 如果没数据了，必须手动抛出异常通知 for 循环停止
            raise StopIteration

# --- 测试代码 ---
print("--- 开始手动挡迭代 ---")
my_iter = MyRange(3)

print(next(my_iter)) # 输出 0
print(next(my_iter)) # 输出 1
print(next(my_iter)) # 输出 2
# print(next(my_iter)) # 再运行这行就会报错 StopIteration

# --- 放在 for 循环里自动跑 ---
print("\n--- For 循环自动处理异常 ---")
for i in MyRange(3):
    print(i)
# %%
