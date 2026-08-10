# Whisper 切片 1 测试说明

## 运行环境要求

- Windows 10/11
- Python 3.8+

## 快速测试

### 方法 1：使用简化测试脚本（推荐）

此方法**无需虚拟环境**，直接在系统 Python 中运行：

```bash
# 1. 进入 whisper 目录
cd C:\projects\lingua-workbench\whisper

# 2. 安装依赖（如果还没有）
pip install yt-dlp fastapi httpx

# 3. 运行测试
python tests/test_simple.py
```

### 方法 2：使用 pytest

```bash
# 1. 进入 whisper 目录
cd C:\projects\lingua-workbench\whisper

# 2. 激活虚拟环境
.venv\Scripts\activate

# 3. 安装 pytest 和 httpx（如果还没有）
pip install pytest httpx

# 4. 运行测试
pytest tests/test_info_endpoint.py -v
```

**注意**：如果 pytest 使用了系统 Python 而不是虚拟环境，请尝试：
```bash
# 使用虚拟环境中的 Python 直接运行
.venv\Scripts\python.exe tests/test_simple.py
```

## 测试内容

### 后端测试

1. **yt-dlp 服务模块测试**
   - VideoInfo 数据类
   - get_video_info 函数（mock）
   - 错误处理

2. **FastAPI 端点测试**
   - /info 端点成功情况
   - /info 端点错误情况（无效 URL）

### 前端测试

```bash
# 1. 进入 frontend 目录
cd C:\projects\lingua-workbench\frontend

# 2. 运行测试
npx vitest run src/components/whisper/__tests__/UrlInput.test.ts
```

## 常见问题

### Q: 找不到 fastapi 模块

**原因**：使用了系统 Python，而不是虚拟环境

**解决**：
```bash
# 确保激活虚拟环境
.venv\Scripts\activate

# 检查 Python 路径
where python
# 应该显示：C:\projects\lingua-workbench\whisper\.venv\Scripts\python.exe
```

### Q: 找不到 yt_dlp 模块

**原因**：虚拟环境中没有安装 yt-dlp

**解决**：
```bash
# 激活虚拟环境
.venv\Scripts\activate

# 安装 yt-dlp
pip install yt-dlp
```

### Q: 找不到 httpx 模块

**原因**：测试 FastAPI 需要 httpx

**解决**：
```bash
# 激活虚拟环境
.venv\Scripts\activate

# 安装 httpx
pip install httpx
```

## 集成测试

测试通过后，可以启动服务进行集成测试：

```bash
# 终端 1：启动 Whisper 后端
cd C:\projects\lingua-workbench\whisper
.venv\Scripts\activate
uvicorn whisper_api:app --reload --port 8001

# 终端 2：启动前端
cd C:\projects\lingua-workbench\frontend
npm run dev
```

然后访问：`http://localhost:5173/whisper`

## 测试清单

- [ ] 后端测试通过（python tests/run_tests.py）
- [ ] 前端测试通过（npx vitest run）
- [ ] /info 端点可以正常访问
- [ ] 输入 YouTube URL 可以显示视频预览
- [ ] 无效 URL 显示错误提示
- [ ] 页面加载正常，无控制台错误
