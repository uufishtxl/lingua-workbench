from huey import SqliteHuey
import whisper
import os
import database
import frontend_agent
from dotenv import load_dotenv
from yt_dlp_service import download_audio, YtdlpError

load_dotenv()

# 1. 配置 Huey 使用本地文件做数据库
huey = SqliteHuey('whisper_queue.db')

RESULTS_DIR = "results"
UPLOAD_DIR = "upload"
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 加载模型
print("--- Worker: 正在加载 Whisper 模型 ---")
model = whisper.load_model("small", device="cpu")
print("--- Worker: 模型加载完毕  ---")

# 3. 定义任务
@huey.task()
def run_whisper_task(task_id, file_path, skip_llm=False):
    """
    这个函数在后台 Worker 里运行，不会卡住 API
    skip_llm: 如果为 True，跳过 LLM 意图分析，只返回纯文本转写结果
    """
    print(f"--- Worker: 开始处理任务 {task_id} (skip_llm={skip_llm}) ---")
    database.update_task_status(task_id, "processing")

    
    try:
        # 这里是调用本地的 Whisper 服务来进行 Speech To Text 的服务，只要给出路径，ffmpeg 会自动读取这个路径
        # 这个项目原作使用的是 OpenAI 的 Whisper 服务，需要通过with语句读取文件，上传音频文件给 OpenAI。
        result = model.transcribe(file_path, fp16=False)
        # 真实场景里，这里应该把结果存进数据库
        # 这里为了演示，只打印出来，并把结果写到一个文本文件里
        # base_name = os.path.splitext(os.path.basename(file_path))[0]
        # output_txt = os.path.join(RESULTS_DIR, base_name + '.txt')
        # with open(output_txt, "w", encoding="utf-8") as f:
        #     f.write(result["text"])
        # print("--- Worker: 处理完毕，结果写入文件：{}".format(output_txt))
        
        
        # 4. 调用 LangChain 处理意图 (如果有 API KEY 且没有 skip_llm)
        final_result = result["text"].strip()
        # 无论是否 skip_llm，都构造带时间戳的 segments（corpus TTS 流程依赖）
        segments_json = None
        if "segments" in result:
            import json
            segments = []
            for seg in result["segments"]:
                segments.append({
                    "text": seg["text"].strip(),
                    "start": round(seg["start"], 2),
                    "end": round(seg["end"], 2)
                })
            segments_json = json.dumps(segments, ensure_ascii=False)
            if segments:
                actual_duration = round(segments[-1]["end"])
                database.update_task_duration(task_id, actual_duration)
                print(f"--- Worker: 实际时长: {actual_duration}s ---")

        if skip_llm:
            # 跳过 LLM：返回 segments JSON（含时间戳）；无 segments 时返回空数组
            final_result = segments_json if segments_json else "[]"
            print(f"--- Worker: 跳过 LLM 结果: {final_result[:200]} ---")
        else:
            api_key = os.getenv("DEEPSEEK_API_KEY")
            if api_key:
                print(f"--- Worker: 正在调用 LLM 分析意图, {final_result} ---")
                llm_result = frontend_agent.process_voice_command(result["text"], api_key)
                # 将 LLM 的结果合并到最终结果中，或者直接存 JSON
                # 这里我们把 LLM 的结果转成字符串存进去，或者存成 JSON 字符串
                import json
                """
                json.dump(obj): 接收 Python 对象（如字典、列表） → 转换成 JSON 字符串；
                json.loads(str): 接收 JSON 字符串 → 转换成 Python 对象（如字典、列表）
                """
                final_result = json.dumps(llm_result, ensure_ascii=False)
                print("--- Worker: LLM 分析完毕: {} ---".format(final_result))

        database.update_task_status(task_id, "completed", result=final_result)
        return final_result

    except Exception as e:
        print("--- Worker: 处理失败：{}".format(e))
        database.update_task_status(task_id, "failed", result=str(e))
        return str(e)


@huey.task()
def run_url_transcribe_task(task_id, url, skip_llm=False, whisper_model="base"):
    """
    通过 URL 下载音频并进行转录
    """
    print(f"--- Worker: 开始处理 URL 转录任务 {task_id} ---")
    database.update_task_status(task_id, "processing")
    
    file_path = None
    try:
        # 1. 下载音频
        print(f"--- Worker: 正在下载音频: {url} ---")
        file_path = download_audio(url, UPLOAD_DIR)
        print(f"--- Worker: 音频下载完成: {file_path} ---")
        
        # 2. 调用 Whisper 转录
        print(f"--- Worker: 正在转录，模型: {whisper_model} ---")
        result = model.transcribe(file_path, fp16=False)
        
        # 3. 处理结果
        final_result = result["text"].strip()
        
        # 如果有 segments，保存带时间戳的结果
        if "segments" in result:
            import json
            segments = []
            for seg in result["segments"]:
                segments.append({
                    "text": seg["text"].strip(),
                    "start": round(seg["start"], 2),
                    "end": round(seg["end"], 2)
                })
            final_result = json.dumps(segments, ensure_ascii=False)
            
            # 用 Whisper 实际时长更新 duration
            if segments:
                actual_duration = round(segments[-1]["end"])
                database.update_task_duration(task_id, actual_duration)
                print(f"--- Worker: 实际时长: {actual_duration}s ---")
        
        print(f"--- Worker: 转录完成 ---")
        database.update_task_status(task_id, "completed", result=final_result)
        return final_result
        
    except YtdlpError as e:
        error_msg = f"下载失败: {e}"
        print(f"--- Worker: {error_msg} ---")
        database.update_task_status(task_id, "failed", result=error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"转录失败: {e}"
        print(f"--- Worker: {error_msg} ---")
        database.update_task_status(task_id, "failed", result=error_msg)
        return error_msg
    finally:
        # 清理下载的音频文件
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"--- Worker: 清理临时文件: {file_path} ---")
            except:
                pass