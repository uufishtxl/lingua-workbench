# 路径拼接

# %%
import os
p = os.path.join('data', 'uploads', 'image.png')
print(p)

print(f"name is {os.path.basename(p)}")
print(f"stem is {os.path.splitext(p)[0]}")
print(f"suffix is {os.path.splitext(p)[1]}")
print(f"parent is {os.path.dirname(p)}")

# %%
from pathlib import Path
p2 = Path('data') / 'uploads' / 'image.png'
print(p2)

# %%
print(f"name is {p2.name}")
print(f"stem is {p2.stem}")
print(f"suffix is {p2.suffix}")
print(f"parent is {p2.parent}")
# %%
# 创建文件夹
# os.path
if not os.path.exists('data'):
    os.makedirs('data')
# %%
# pathlib
newp = Path('pathlib-create-folder')
newp.mkdir(parents=True, exist_ok=True)
# %%
