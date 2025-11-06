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
from dj_rest_auth.registration.views import RegisterView
from dj_rest_auth.jwt_auth import get_refresh_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/token/refresh/', get_refresh_view().as_view(), name='token_refresh'),

    # --- (1) 【新增】 dj-rest-auth 的 API 路由 ---
    # 这会“自动”为你创建好以下 URL (都以 /api/auth/ 开头):
    # /api/auth/login/ (用于登录)
    # /api/auth/logout/ (用于登出)
    # /api/auth/password/reset/ (用于重置密码)
    # /api/auth/register/ (用于注册, 因为我们装了 dj_rest_auth.registration)
    # ...等等
    path('api/auth/', include('dj_rest_auth.urls')),

    path('api/auth/registration/', RegisterView.as_view(), name='rest_register'),
    path('api/auth/accounts/', include('allauth.urls')),
    # --- (2) 【修改】把你 V1 的 App 也移到 API 专区 ---
    # 我们把你 phrase_log App 的所有 URL 也放到 /api/ 下
    # (这样我们的 Vue 以后就知道，所有的数据都去 /api/ 里找)
    path('api/v1/', include('phrase_log.urls')),

    # 功能路由

]
