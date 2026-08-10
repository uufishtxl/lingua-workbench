#!/usr/bin/env python3
"""
简单的测试脚本，可以直接运行
无需 pytest，使用 Python 内置的 unittest

运行方法：
1. cd /workspace/whisper
2. .venv\\Scripts\\activate
3. python tests/run_tests.py
"""
import sys
import os
from unittest.mock import Mock, patch

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_yt_dlp_service():
    """测试 yt-dlp 服务模块"""
    print("=" * 60)
    print("测试 yt-dlp 服务模块")
    print("=" * 60)
    
    try:
        from yt_dlp_service import get_video_info, VideoInfo, InvalidUrlError
        print("✓ 成功导入 yt_dlp_service")
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        print("请确保在虚拟环境中运行，并安装 yt-dlp: pip install yt-dlp")
        return False
    
    # 测试 VideoInfo 数据类
    try:
        info = VideoInfo(
            title="Test Video",
            thumbnail_url="https://example.com/thumb.jpg",
            duration=120,
            author="Test Author",
            platform="youtube",
            url="https://www.youtube.com/watch?v=test123"
        )
        assert info.title == "Test Video"
        assert info.duration == 120
        print("✓ VideoInfo 数据类正常")
    except Exception as e:
        print(f"✗ VideoInfo 数据类错误: {e}")
        return False
    
    # 测试 mock get_video_info
    try:
        mock_info = VideoInfo(
            title="Mock Video",
            thumbnail_url="https://example.com/mock.jpg",
            duration=60,
            author="Mock Author",
            platform="youtube",
            url="https://www.youtube.com/watch?v=mock123"
        )
        
        with patch('yt_dlp_service.yt_dlp.YoutubeDL') as mock_youtube_dl:
            mock_ydl_instance = Mock()
            mock_ydl_instance.extract_info.return_value = {
                'title': 'Mock Video',
                'thumbnail': 'https://example.com/mock.jpg',
                'duration': 60,
                'uploader': 'Mock Author',
                'extractor': 'youtube'
            }
            mock_ydl_instance.__enter__ = Mock(return_value=mock_ydl_instance)
            mock_ydl_instance.__exit__ = Mock(return_value=False)
            mock_youtube_dl.return_value = mock_ydl_instance
            
            result = get_video_info("https://www.youtube.com/watch?v=mock123")
            assert result.title == "Mock Video"
            assert result.duration == 60
            print("✓ get_video_info 函数正常（mock）")
    except Exception as e:
        print(f"✗ get_video_info 函数错误: {e}")
        return False
    
    print()
    return True


def test_fastapi_endpoint():
    """测试 FastAPI 端点"""
    print("=" * 60)
    print("测试 FastAPI 端点")
    print("=" * 60)
    
    try:
        from fastapi.testclient import TestClient
        print("✓ 成功导入 FastAPI TestClient")
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        print("请安装依赖：pip install httpx")
        return False
    
    try:
        from whisper_api import app
        from yt_dlp_service import VideoInfo, InvalidUrlError
        print("✓ 成功导入 FastAPI 应用和 yt_dlp_service")
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False
    
    try:
        client = TestClient(app)
        print("✓ 创建测试客户端成功")
    except Exception as e:
        print(f"✗ 创建测试客户端失败: {e}")
        return False
    
    # 测试 /info 端点
    try:
        with patch('whisper_api.get_video_info') as mock_get_video_info:
            mock_info = VideoInfo(
                title="Test Video",
                thumbnail_url="https://example.com/thumb.jpg",
                duration=120,
                author="Test Author",
                platform="youtube",
                url="https://www.youtube.com/watch?v=test123"
            )
            mock_get_video_info.return_value = mock_info
            
            response = client.get("/info", params={"url": "https://www.youtube.com/watch?v=test123"})
            
            assert response.status_code == 200
            data = response.json()
            assert data["title"] == "Test Video"
            assert data["duration"] == 120
            print("✓ /info 端点正常（成功情况）")
    except Exception as e:
        print(f"✗ /info 端点错误: {e}")
        return False
    
    # 测试无效 URL
    try:
        with patch('whisper_api.get_video_info') as mock_get_video_info:
            mock_get_video_info.side_effect = InvalidUrlError("Invalid URL")
            
            response = client.get("/info", params={"url": "invalid-url"})
            
            assert response.status_code == 400
            assert "Invalid URL" in response.json()["detail"]
            print("✓ /info 端点正常（无效 URL）")
    except Exception as e:
        print(f"✗ /info 端点错误（无效 URL）: {e}")
        return False
    
    print()
    return True


def main():
    """主测试函数"""
    print("Whisper 切片 1 测试")
    print("=" * 60)
    print()
    
    results = []
    
    # 测试 yt-dlp 服务
    results.append(test_yt_dlp_service())
    
    # 测试 FastAPI 端点
    results.append(test_fastapi_endpoint())
    
    # 汇总结果
    print("=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✓ 所有测试通过 ({passed}/{total})")
        print()
        print("切片 1 后端部分实现正确！")
        print("接下来可以启动服务进行集成测试：")
        print("1. uvicorn whisper_api:app --reload --port 8001")
        print("2. 访问 http://localhost:8001/docs 查看 API 文档")
        print("3. 测试 /info 端点")
        return 0
    else:
        print(f"✗ 部分测试失败 ({passed}/{total})")
        print()
        print("请检查错误信息并修复问题")
        return 1


if __name__ == "__main__":
    sys.exit(main())
