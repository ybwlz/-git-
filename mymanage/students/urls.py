from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    # 示例URL模式，后续根据实际需要添加
    path('list/', views.student_list, name='list'),
    path('detail/<int:pk>/', views.student_detail, name='detail'),
]
