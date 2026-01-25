"""
URL Configuration for Documentation Assistant
"""
from django.urls import path
from . import views

urlpatterns = [
    path('chat/', views.ChatView.as_view(), name='doc_chat'),
    path('chat/stream/', views.ChatStreamView.as_view(), name='doc_chat_stream'),
    path('status/', views.IndexStatusView.as_view(), name='doc_index_status'),
]
