"""
yt-dlp 服务模块
封装 yt-dlp 调用，提供统一接口获取视频元数据和下载音频
"""
import yt_dlp
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class VideoInfo:
    """视频元数据"""
    title: str
    thumbnail_url: str
    duration: int  # 秒
    author: str
    platform: str  # youtube, bilibili, etc.
    url: str  # 原始 URL


class YtdlpError(Exception):
    """yt-dlp 错误基类"""
    pass


class InvalidUrlError(YtdlpError):
    """无效 URL 错误"""
    pass


class VideoNotFoundError(YtdlpError):
    """视频不存在错误"""
    pass


class PrivateVideoError(YtdlpError):
    """私有视频错误"""
    pass


class NetworkError(YtdlpError):
    """网络错误"""
    pass


def get_video_info(url: str) -> VideoInfo:
    """
    获取视频元数据
    
    Args:
        url: 视频 URL
        
    Returns:
        VideoInfo: 视频元数据
        
    Raises:
        InvalidUrlError: URL 无效
        VideoNotFoundError: 视频不存在
        PrivateVideoError: 私有视频
        NetworkError: 网络错误
    """
    logger.info(f"获取视频信息: {url}")
    
    # 清理 URL，移除播放列表参数
    if '&list=' in url:
        url = url.split('&list=')[0]
        logger.info(f"清理后的 URL: {url}")
    
    # yt-dlp 配置：获取完整信息，不下载
    ydl_opts = {
        'quiet': True,  # 静默模式
        'no_warnings': True,  # 不显示警告
        'skip_download': True,  # 不下载视频
        'cookiefile': 'cookies.txt',
        'socket_timeout': 30,  # 30秒超时
        'proxy': 'http://127.0.0.1:7897',
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 提取视频信息
            info = ydl.extract_info(url, download=False)
            
            if info is None:
                raise VideoNotFoundError(f"无法获取视频信息: {url}")
            
            # 处理播放列表：只取第一个视频
            if 'entries' in info:
                entries = list(info['entries'])
                if not entries:
                    raise VideoNotFoundError(f"播放列表为空: {url}")
                info = entries[0]
            
            # 构建 VideoInfo
            # 优先使用 thumbnails 列表中的最后一个（通常是最高质量）
            thumbnail_url = ''
            if 'thumbnails' in info and info['thumbnails']:
                # 取最后一个缩略图
                thumbnail_url = info['thumbnails'][-1].get('url', '')
            elif 'thumbnail' in info:
                thumbnail_url = info.get('thumbnail', '')
            
            video_info = VideoInfo(
                title=info.get('title', '未知标题'),
                thumbnail_url=thumbnail_url,
                duration=int(info.get('duration', 0)),
                author=info.get('uploader', info.get('channel', '未知作者')),
                platform=info.get('extractor', 'unknown'),
                url=url
            )
            
            logger.info(f"获取视频信息成功: {video_info.title}")
            return video_info
            
    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e).lower()
        logger.error(f"yt-dlp 原始错误: {e}")
        
        # 解析错误类型
        if 'invalid url' in error_msg or 'unsupported url' in error_msg:
            raise InvalidUrlError(f"无效的 URL: {url}")
        elif 'video unavailable' in error_msg or 'not available' in error_msg:
            raise VideoNotFoundError(f"视频不存在或不可用: {url}")
        elif 'private video' in error_msg:
            raise PrivateVideoError(f"私有视频，无法访问: {url}")
        elif 'sign in' in error_msg or 'bot' in error_msg:
            raise NetworkError(f"YouTube 需要验证，请更新 cookies: {e}")
        elif 'network' in error_msg or 'timeout' in error_msg:
            raise NetworkError(f"网络错误: {e}")
        else:
            raise YtdlpError(f"获取视频信息失败: {e}")
            
    except Exception as e:
        logger.error(f"获取视频信息时发生未知错误: {e}")
        raise YtdlpError(f"获取视频信息失败: {e}")


def download_audio(url: str, output_path: str = ".") -> str:
    """
    下载音频文件
    
    Args:
        url: 视频 URL
        output_path: 输出目录
        
    Returns:
        str: 下载的音频文件路径
        
    Raises:
        YtdlpError: 下载失败
    """
    logger.info(f"下载音频: {url}")
    
    # 清理 URL，移除播放列表参数
    if '&list=' in url:
        url = url.split('&list=')[0]
        logger.info(f"清理后的 URL: {url}")
    
    # yt-dlp 配置：下载音频
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{output_path}/%(id)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'm4a',
        }],
        'quiet': True,
        'no_warnings': True,
        'cookiefile': 'cookies.txt',
        'noplaylist': True,  # 只下载单个视频，不下载播放列表
        'proxy': 'http://127.0.0.1:7897',
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # FFmpeg 后处理器可能会改变扩展名
            import os
            base_filename = os.path.splitext(filename)[0]
            expected_filename = f"{base_filename}.m4a"
            
            if os.path.exists(expected_filename):
                logger.info(f"下载完成: {expected_filename}")
                return expected_filename
            elif os.path.exists(filename):
                logger.info(f"下载完成: {filename}")
                return filename
            else:
                raise YtdlpError(f"下载的文件不存在: {filename}")
                
    except yt_dlp.utils.DownloadError as e:
        logger.error(f"下载失败: {e}")
        raise YtdlpError(f"下载失败: {e}")
    except Exception as e:
        logger.error(f"下载时发生未知错误: {e}")
        raise YtdlpError(f"下载失败: {e}")


# 测试代码
if __name__ == "__main__":
    # 测试获取视频信息
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    try:
        info = get_video_info(test_url)
        print(f"标题: {info.title}")
        print(f"时长: {info.duration}秒")
        print(f"作者: {info.author}")
        print(f"平台: {info.platform}")
        print(f"缩略图: {info.thumbnail_url}")
    except Exception as e:
        print(f"错误: {e}")
