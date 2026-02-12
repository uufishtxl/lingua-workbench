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

    # --- (1) �鞉鰵憓𠺶�?dj-rest-auth �?API 頝舐眏 ---
    # 餈嗘��𡏭䌊�兩�苷蛹雿惩�撱箏末隞乩� URL (�賭誑 /api/auth/ 撘�憭?:
    # /api/auth/login/ (�其��餃�)
    # /api/auth/logout/ (�其��餃枂)
    # /api/auth/password/reset/ (�其��滨蔭撖��)
    # /api/auth/register/ (�其�瘜典�, �牐蛹�睲賑鋆�� dj_rest_auth.registration)
    # ...蝑厩�
    path('api/auth/', include('dj_rest_auth.urls')),

    path('api/auth/registration/', RegisterView.as_view(), name='rest_register'),
    path('api/auth/accounts/', include('allauth.urls')),
    # --- (2) �𣂷耨�嫘�烐�雿?V1 �?App 銋毺宏�?API 銝枏躹 ---
    # �睲賑�𠹺� phrase_log App ����?URL 銋�𦆮�?/api/ 銝?
    # (餈蹱甅�睲賑�?Vue 隞亙�撠梁䰻�橒����厩��唳旿�賢縧 /api/ �峕𪄳)
    path('api/v1/', include('sample_project.api_v1_urls')),

    # AI Analysis API
    path('api/ai/', include('ai_analysis.urls')),

    # Documentation Assistant (DITA RAG Chatbot)
    path('api/doc-assistant/', include('doc_assistant.urls')),
    path('api/sandbox/', include('sandbox.urls')),

    # Scripts (Fanfr.com script parser)
    path('api/scripts/', include('scripts.urls')),

    # �蠘�頝舐眏

]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
