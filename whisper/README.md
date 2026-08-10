# 批量重命名音频脚本

`batch_rename_by_transcribe.py` —— 根据 Whisper 语音转录结果，自动识别音频内容并按统一范式重命名。

## 命名范式

| 格式 | 示例 | 含义 |
|------|------|------|
| `sf_{册}_{书}_{页}` | `sf_1_pb_p83` | Super Safari 1, Pupil's Book, Page 83 |
| `sf_{册}_{书}_{页}` | `sf_1_ab_p12` | Super Safari 1, Activity Book, Page 12 |
| `sf_{册}_{书}_{页}_{部分}` | `sf_1_pb_p19_4_listen_and_act` | 同页不同部分（advanced 模式） |

- `pb` = Pupil's Book
- `ab` = Activity Book

## 基本用法

```bash
# Dry-Run 模式（默认）—— 只打印预览，不执行任何文件操作
python batch_rename_by_transcribe.py

# 实际执行重命名
python batch_rename_by_transcribe.py --execute

# Advanced 两轮模式
python batch_rename_by_transcribe.py --advanced

# Advanced + 实际执行
python batch_rename_by_transcribe.py --advanced --execute
```

## 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--execute` | `False` | 实际执行重命名。未传入时为 Dry-Run 模式，仅打印 `原文件名 -> 新文件名`，**不会修改任何文件** |
| `--advanced` | `False` | 启用两轮扫描模式（详见下方） |
| `--port` | `8000` | 本地 Whisper 服务端口 |

## 运行模式

### 普通模式（默认）

- 只运行一轮，截取每个音频的**前 4 秒**
- 已符合范式（`sf_数字_` 开头）的文件自动跳过
- 匹配失败的文件直接跳过
- 目标文件名冲突时跳过

### Advanced 模式（`--advanced`）

分三步执行：

**第一步：4 秒扫描**
- 截取前 4 秒送 Whisper 转录
- 匹配成功 → 记录任务（不立即重命名）
- 匹配失败 → 加入第二轮重试队列

**第二步：8 秒扫描**
- 对第一轮未匹配的文件截取前 8 秒重试
- 如果 8 秒转录到更多内容（如 "Pupil's Book Page 19 4 Listen and Act"），自动加后缀：
  - 有 Karaoke → `_4_listen_and_do_karaoke`
  - 无 Karaoke → `_4_listen_and_act`（数字 + 3 个单词）

**第三步：统一执行**
- 按收集到的任务统一重命名
- 同名冲突时，第一个保留原位，后续的移到 `duplicates/` 文件夹
- `duplicates/` 内如果还冲突，自动加序号（如 `sf_1_pb_p83_2.wma`）

## 文件过滤规则

- **跳过**：文件名以 `sf_数字_` 开头（如 `sf_1_pb_p83.wma`），视为已符合范式
- **处理**：其他所有音频文件（如 `57 劗喈Κ_57.wma`）

支持的音频格式：`.mp3` `.wav` `.wma` `.m4a` `.ogg` `.flac` `.aac` `.opus` `.mp4`

## 日志与报告

### 终端输出

运行时实时打印每个文件的处理结果：

```
▶ 第一轮（4s）匹配
  ▶ 07 劗喈Κ_7.wma
    📌 匹配: sf_1_pb_p7

▶ 执行重命名（共 1 个任务）
  ✅ 07 劗喈Κ_7.wma  ->  sf_1_pb_p7.wma  [原地] (Dry-Run)
```

### 报告文件

每次运行结束后自动在脚本同目录下生成 `rename_report.txt`，包含：

- **未匹配页面信息的音频** —— Whisper 转录后仍无法识别页面的文件
- **冲突/移到 duplicates 的文件** —— 目标文件名已存在的文件

报告路径：`whisper/rename_report.txt`

## 前置要求

1. **ffmpeg**：需要在系统 PATH 中
2. **Whisper 服务**：本地运行的 Whisper API 服务（默认端口 8000）
3. **Python 依赖**：`requests`

```bash
pip install requests
```

## 完整示例

```bash
# 1. 先用 Dry-Run 预览，确认不会误操作
python batch_rename_by_transcribe.py --advanced

# 2. 检查输出和 rename_report.txt
cat rename_report.txt

# 3. 确认无误后，实际执行
python batch_rename_by_transcribe.py --advanced --execute
```
