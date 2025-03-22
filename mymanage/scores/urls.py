from django.urls import path
from . import views

app_name = 'scores'

urlpatterns = [
    # 示例URL模式，后续根据实际需要添加
    path('list/', views.score_list, name='list'),
    path('add/', views.add_score, name='add'),
]
