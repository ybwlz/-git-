from django.urls import path
from . import views

app_name = 'teachers'

urlpatterns = [
    # 示例URL模式，后续根据实际需要添加
    path('list/', views.teacher_list, name='list'),
    path('detail/<int:pk>/', views.teacher_detail, name='detail'),
]
