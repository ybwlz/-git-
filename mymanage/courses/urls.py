from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    # 示例URL模式，后续根据实际需要添加
    path('list/', views.course_list, name='list'),
    path('detail/<int:pk>/', views.course_detail, name='detail'),
]
