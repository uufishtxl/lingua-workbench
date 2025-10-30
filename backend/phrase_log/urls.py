from django.urls import path
from . import views


urlpatterns = [
    # GET (显示表单) 和 POST (处理表单) 
    path("", views.lookup_view, name="home"),
    # 显示 home 页处理 POST 表单后的结果
    path("results/", views.result_view, name="results-page")
]
