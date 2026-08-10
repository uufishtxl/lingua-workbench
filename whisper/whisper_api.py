# whisper_api.py
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from tasks import run_whisper_task, run_url_transcribe_task
import shutil
import uuid
import os
from fastapi.staticfiles import StaticFiles
import database
from yt_dlp_service import get_video_info, download_audio, YtdlpError, InvalidUrlError, VideoNotFoundError, PrivateVideoError, NetworkError

UPLOAD_DIR = "upload"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI()

# 生产环境提醒：如果以后要上线，建议把 allow_origins=["*"] 改成具体的域名列表（比如 ["https://your-domain.com"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化数据库
database.init_db()

# 挂载静态文件目录
os.makedirs("static", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.post("/transcribe")
async def create_task_endpoint(
    file: UploadFile = File(...), 
    skip_llm: bool = False,
    whisper_model: str = "base"
):
    """上传音频文件进行转录"""
    file_name = file.filename
    unique_filename = f"upload_{file_name}_{uuid.uuid4()}.mp3"
    
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    task_id = database.create_task(unique_filename, whisper_model=whisper_model)
    run_whisper_task(task_id, file_path, skip_llm)

    return {
        "status": "queued",
        "task_id": task_id,
        "message": "您的任务已在后台排队，请稍后查看结果文件。"
    }


@app.post("/transcribe-url")
async def create_url_task_endpoint(
    url: str = Query(..., description="视频 URL"),
    skip_llm: bool = False,
    whisper_model: str = "base",
    video_title: str = Query("", description="视频标题"),
    thumbnail_url: str = Query("", description="缩略图 URL"),
    duration: int = Query(0, description="时长（秒）"),
):
    """通过 URL 进行转录"""
    try:
        # 直接创建任务，不重复获取视频信息
        task_id = database.create_task(
            filename=url,
            source_url=url,
            video_title=video_title or url,
            thumbnail_url=thumbnail_url,
            duration=duration,
            whisper_model=whisper_model
        )
        
        # 异步执行转录任务
        run_url_transcribe_task(task_id, url, skip_llm, whisper_model)
        
        return {
            "status": "queued",
            "task_id": task_id,
            "message": "您的任务已在后台排队，请稍后查看结果文件。"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建转录任务失败: {e}")


@app.get("/task/{task_id}")
async def get_task_status(task_id: int):
    """获取任务状态"""
    task = database.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.get("/tasks")
async def get_tasks_endpoint(limit: int = Query(50, description="返回数量")):
    """获取任务列表"""
    tasks = database.get_tasks(limit)
    return tasks


@app.post("/tasks/{task_id}/pin")
async def pin_task_endpoint(task_id: int):
    """置顶任务"""
    task = database.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    database.pin_task(task_id)
    return {"message": "已置顶"}


@app.post("/tasks/{task_id}/unpin")
async def unpin_task_endpoint(task_id: int):
    """取消置顶"""
    task = database.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    database.unpin_task(task_id)
    return {"message": "已取消置顶"}


@app.delete("/tasks/{task_id}")
async def delete_task_endpoint(task_id: int):
    """删除任务"""
    task = database.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    database.delete_task(task_id)
    return {"message": "已删除"}


@app.post("/tasks/{task_id}/retry")
async def retry_task_endpoint(task_id: int):
    """重试失败的任务"""
    task = database.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task['status'] != 'failed':
        raise HTTPException(status_code=400, detail="只能重试失败的任务")
    
    # 重新提交任务
    database.update_task_status(task_id, 'queued')
    if task['source_url']:
        from tasks import run_url_transcribe_task
        run_url_transcribe_task(task_id, task['source_url'], whisper_model=task.get('whisper_model', 'base'))
    else:
        raise HTTPException(status_code=400, detail="该任务没有源 URL，无法重试")
    
    return {"message": "已重新提交"}


@app.get("/info")
async def get_video_info_endpoint(url: str = Query(..., description="视频 URL")):
    """
    获取视频元数据
    
    Returns:
        {
            "title": "视频标题",
            "thumbnail_url": "缩略图 URL",
            "duration": 120,  # 秒
            "author": "作者",
            "platform": "youtube"
        }
    """
    try:
        info = get_video_info(url)
        return {
            "title": info.title,
            "thumbnail_url": info.thumbnail_url,
            "duration": info.duration,
            "author": info.author,
            "platform": info.platform,
            "url": info.url
        }
    except InvalidUrlError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except VideoNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PrivateVideoError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except NetworkError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except YtdlpError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取视频信息失败: {e}")