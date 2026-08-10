#!/usr/bin/env python3
"""
最简单的测试脚本 - 直接在系统 Python 中运行
无需虚拟环境，无需额外依赖

运行方法：
python tests/test_simple.py
"""
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """测试导入"""
    print("=" * 60)
    print("测试 1: 检查导入")
    print("=" * 60)
    
    errors = []
    
    # 测试 yt_dlp
    try:
        import yt_dlp
        print(f"✓ yt-dlp 已安装 (版本: {yt_dlp.version.__version__})")
    except ImportError:
        errors.append("yt-dlp 未安装")
        print("✗ yt-dlp 未安装")
    
    # 测试 fastapi
    try:
        import fastapi
        print(f"✓ fastapi 已安装 (版本: {fastapi.__version__})")
    except ImportError:
        errors.append("fastapi 未安装")
        print("✗ fastapi 未安装")
    
    # 测试 httpx（用于测试）
    try:
        import httpx
        print(f"✓ httpx 已安装 (版本: {httpx.__version__})")
    except ImportError:
        errors.append("httpx 未安装（测试需要）")
        print("✗ httpx 未安装（测试需要）")
    
    if errors:
        print()
        print("缺少依赖，请安装：")
        print("pip install yt-dlp fastapi httpx")
        return False
    
    print()
    return True


def test_yt_dlp_service():
    """测试 yt-dlp 服务模块"""
    print("=" * 60)
    print("测试 2: yt-dlp 服务模块")
    print("=" * 60)
    
    try:
        from yt_dlp_service import get_video_info, VideoInfo, InvalidUrlError
        print("✓ 成功导入 yt_dlp_service")
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
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
    
    # 测试 InvalidUrlError
    try:
        error = InvalidUrlError("Invalid URL")
        assert str(error) == "Invalid URL"
        print("✓ InvalidUrlError 异常类正常")
    except Exception as e:
        print(f"✗ InvalidUrlError 异常类错误: {e}")
        return False
    
    print()
    return True


def test_fastapi_app():
    """测试 FastAPI 应用"""
    print("=" * 60)
    print("测试 3: FastAPI 应用")
    print("=" * 60)
    
    try:
        from whisper_api import app
        print("✓ 成功导入 FastAPI 应用")
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False
    
    # 检查路由
    routes = [route.path for route in app.routes]
    
    if "/info" in routes:
        print("✓ /info 端点已注册")
    else:
        print("✗ /info 端点未注册")
        return False
    
    if "/task/{task_id}" in routes:
        print("✓ /task/{task_id} 端点已注册")
    else:
        print("✗ /task/{task_id} 端点未注册")
        return False
    
    print()
    return True


def test_whisper_api_endpoint():
    """测试 /info 端点（需要 httpx）"""
    print("=" * 60)
    print("测试 4: /info 端点")
    print("=" * 60)
    
    try:
        from fastapi.testclient import TestClient
        print("✓ 成功导入 TestClient")
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        print("跳过此测试（需要 httpx）")
        return True  # 跳过但不失败
    
    try:
        from whisper_api import app
        from yt_dlp_service import VideoInfo, InvalidUrlError
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False
    
    try:
        client = TestClient(app)
        print("✓ 创建测试客户端成功")
    except Exception as e:
        print(f"✗ 创建测试客户端失败: {e}")
        return False
    
    # 测试 /info 端点（使用 mock）
    try:
        from unittest.mock import patch
        
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
    print("Whisper 切片 1 简化测试")
    print("=" * 60)
    print()
    print("说明：此测试脚本可以直接在系统 Python 中运行")
    print("无需虚拟环境，无需 pytest")
    print()
    
    results = []
    
    # 测试导入
    results.append(test_imports())
    
    # 如果导入失败，提前退出
    if not results[-1]:
        print("=" * 60)
        print("测试失败：缺少依赖")
        print("=" * 60)
        return 1
    
    # 测试 yt-dlp 服务
    results.append(test_yt_dlp_service())
    
    # 测试 FastAPI 应用
    results.append(test_fastapi_app())
    
    # 测试 /info 端点
    results.append(test_whisper_api_endpoint())
    
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
        print()
        print("接下来可以启动服务进行集成测试：")
        print("1. 启动 Whisper 后端：")
        print("   cd C:\\projects\\lingua-workbench\\whisper")
        print("   .venv\\Scripts\\activate")
        print("   uvicorn whisper_api:app --reload --port 8001")
        print()
        print("2. 启动前端：")
        print("   cd C:\\projects\\lingua-workbench\\frontend")
        print("   npm run dev")
        print()
        print("3. 访问：http://localhost:5173/whisper")
        return 0
    else:
        print(f"✗ 部分测试失败 ({passed}/{total})")
        print()
        print("请检查错误信息并修复问题")
        return 1


if __name__ == "__main__":
    sys.exit(main())
