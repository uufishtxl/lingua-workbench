"""
测试 /info 端点
这些测试可以在 Windows 上运行，需要安装 pytest

运行方法：
1. cd /workspace/whisper
2. .venv\Scripts\activate
3. pip install pytest httpx
4. pytest tests/test_info_endpoint.py -v
"""
import sys
import os

# 确保使用虚拟环境
if 'venv' not in sys.executable:
    print("警告：请确保使用虚拟环境运行测试")
    print("运行：.venv\Scripts\activate")
    print()

try:
    import pytest
    from unittest.mock import Mock, patch
    from fastapi.testclient import TestClient
except ImportError as e:
    print(f"导入错误：{e}")
    print("请安装依赖：pip install pytest httpx fastapi")
    sys.exit(1)

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入 FastAPI 应用
from whisper_api import app
from yt_dlp_service import VideoInfo, InvalidUrlError, VideoNotFoundError

# 创建测试客户端
client = TestClient(app)


class TestInfoEndpoint:
    """测试 /info 端点"""

    @patch('whisper_api.get_video_info')
    def test_get_video_info_success(self, mock_get_video_info):
        """测试成功获取视频信息"""
        # 模拟返回数据
        mock_info = VideoInfo(
            title="Test Video",
            thumbnail_url="https://example.com/thumbnail.jpg",
            duration=120,
            author="Test Author",
            platform="youtube",
            url="https://www.youtube.com/watch?v=test123"
        )
        mock_get_video_info.return_value = mock_info

        # 发送请求
        response = client.get("/info", params={"url": "https://www.youtube.com/watch?v=test123"})

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Video"
        assert data["thumbnail_url"] == "https://example.com/thumbnail.jpg"
        assert data["duration"] == 120
        assert data["author"] == "Test Author"
        assert data["platform"] == "youtube"

    @patch('whisper_api.get_video_info')
    def test_get_video_info_invalid_url(self, mock_get_video_info):
        """测试无效 URL"""
        # 模拟抛出错误
        mock_get_video_info.side_effect = InvalidUrlError("Invalid URL")

        # 发送请求
        response = client.get("/info", params={"url": "invalid-url"})

        # 验证响应
        assert response.status_code == 400
        assert "Invalid URL" in response.json()["detail"]

    @patch('whisper_api.get_video_info')
    def test_get_video_info_not_found(self, mock_get_video_info):
        """测试视频不存在"""
        # 模拟抛出错误
        mock_get_video_info.side_effect = VideoNotFoundError("Video not found")

        # 发送请求
        response = client.get("/info", params={"url": "https://www.youtube.com/watch?v=notfound"})

        # 验证响应
        assert response.status_code == 404
        assert "Video not found" in response.json()["detail"]

    def test_get_video_info_missing_url(self):
        """测试缺少 URL 参数"""
        # 发送请求（不带 url 参数）
        response = client.get("/info")

        # 验证响应
        assert response.status_code == 422  # Unprocessable Entity


class TestYtdlpService:
    """测试 yt-dlp 服务模块"""

    @patch('yt_dlp_service.yt_dlp.YoutubeDL')
    def test_get_video_info_success(self, mock_youtube_dl):
        """测试成功获取视频信息"""
        # 模拟 yt-dlp 返回数据
        mock_info = {
            'title': 'Test Video',
            'thumbnail': 'https://example.com/thumbnail.jpg',
            'duration': 120,
            'uploader': 'Test Author',
            'extractor': 'youtube'
        }
        
        mock_ydl_instance = Mock()
        mock_ydl_instance.extract_info.return_value = mock_info
        mock_ydl_instance.__enter__ = Mock(return_value=mock_ydl_instance)
        mock_ydl_instance.__exit__ = Mock(return_value=False)
        mock_youtube_dl.return_value = mock_ydl_instance

        # 调用函数
        from yt_dlp_service import get_video_info
        result = get_video_info("https://www.youtube.com/watch?v=test123")

        # 验证结果
        assert result.title == "Test Video"
        assert result.thumbnail_url == "https://example.com/thumbnail.jpg"
        assert result.duration == 120
        assert result.author == "Test Author"
        assert result.platform == "youtube"

    @patch('yt_dlp_service.yt_dlp.YoutubeDL')
    def test_get_video_info_with_playlist(self, mock_youtube_dl):
        """测试播放列表（只取第一个视频）"""
        # 模拟 yt-dlp 返回播放列表
        mock_info = {
            'entries': [
                {
                    'title': 'First Video',
                    'thumbnail': 'https://example.com/thumb1.jpg',
                    'duration': 60,
                    'uploader': 'Author 1',
                    'extractor': 'youtube'
                },
                {
                    'title': 'Second Video',
                    'thumbnail': 'https://example.com/thumb2.jpg',
                    'duration': 90,
                    'uploader': 'Author 2',
                    'extractor': 'youtube'
                }
            ]
        }
        
        mock_ydl_instance = Mock()
        mock_ydl_instance.extract_info.return_value = mock_info
        mock_ydl_instance.__enter__ = Mock(return_value=mock_ydl_instance)
        mock_ydl_instance.__exit__ = Mock(return_value=False)
        mock_youtube_dl.return_value = mock_ydl_instance

        # 调用函数
        from yt_dlp_service import get_video_info
        result = get_video_info("https://www.youtube.com/playlist?list=test")

        # 验证结果（应该返回第一个视频）
        assert result.title == "First Video"
        assert result.duration == 60


# 运行测试的说明
if __name__ == "__main__":
    print("请使用 pytest 运行测试:")
    print("cd /workspace/whisper")
    print("pytest tests/test_info_endpoint.py -v")
