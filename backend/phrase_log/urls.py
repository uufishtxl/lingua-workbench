from django.urls import path
from . import views

urlpatterns = [
    # (我们把 V1 的 'lookup_view' 删掉了)

    # 1. 指向 V1 (重构后) 的 API View
    path('lookup/', views.PhraseLookupAPIView.as_view(), name='phrase-lookup'),

    # 2. 【新增】指向 V1.01 的 History API View
    path('history/', views.HistoryAPIView.as_view(), name='phrase-history'),

    # 3. 【新增】获取所有标签的 API View
    path('tags/', views.TagAPIView.as_view(), name='tag-list'),

    # 4. 【新增】处理单个日志条目的 API View (GET, PUT, PATCH, DELETE)
    path('phraselogs/<int:pk>/', views.PhraseLogDetailAPIView.as_view(), name='phraselog-detail'),
]