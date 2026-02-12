
# %%
import sys
import time

# --- 1. print vs sys.stdout ---
# print 本质上就是包装了 sys.stdout.write，并自动加了换行
print("Hello (print)") 
sys.stdout.write("Hello (stdout)\n") # 必须手动加 \n

# --- 2. 缓冲区的区别 (面试考点) ---
# stdout 是有缓冲的（积攒到一定程度或遇到换行才输出）
sys.stdout.write("正在处理...")
# 如果这时候程序卡住或者 sleep，屏幕上可能什么都看不到，因为字还在缓冲区里
# time.sleep(2) 

# stderr 是无缓冲的（立刻输出，通常用于报错或进度条）
sys.stderr.write("紧急错误！立刻显示！\n")

# --- 3. 怎么把 print 发送到 stderr？ ---
# 这是最 Pythonic 的写法，不需要手动用 sys.stderr.write
print("这是一个错误信息", file=sys.stderr)
# %%
