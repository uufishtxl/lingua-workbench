"""
URL configuration for sample_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from dj_rest_auth.registration.views import RegisterView
from dj_rest_auth.jwt_auth import get_refresh_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/token/refresh/', get_refresh_view().as_view(), name='token_refresh'),

    # --- (1) 【新增�?dj-rest-auth �?API 路由 ---
    # 这会“自动”为你创建好以下 URL (都以 /api/auth/ 开�?:
    # /api/auth/login/ (用于登录)
    # /api/auth/logout/ (用于登出)
    # /api/auth/password/reset/ (用于重置密码)
    # /api/auth/register/ (用于注册, 因为我们装了 dj_rest_auth.registration)
    # ...等等
    path('api/auth/', include('dj_rest_auth.urls')),

    path('api/auth/registration/', RegisterView.as_view(), name='rest_register'),
    path('api/auth/accounts/', include('allauth.urls')),
    # --- (2) 【修改】把�?V1 �?App 也移�?API 专区 ---
    # 我们把你 phrase_log App 的所�?URL 也放�?/api/ �?
    # (这样我们�?Vue 以后就知道，所有的数据都去 /api/ 里找)
    path('api/v1/', include('sample_project.api_v1_urls')),

    # AI Analysis API
    path('api/ai/', include('ai_analysis.urls')),

    # 功能路由

]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
