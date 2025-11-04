from django.urls import path
from . import views

urlpatterns = [
    # (我们把 V1 的 'lookup_view' 删掉了)

    # 1. 指向 V1 (重构后) 的 API View
    path('lookup/', views.PhraseLookupAPIView.as_view(), name='phrase-lookup'),

    # 2. 【新增】指向 V1.01 的 History API View
    path('history/', views.HistoryAPIView.as_view(), name='phrase-history'),
]