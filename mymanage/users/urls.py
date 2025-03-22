from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # 示例URL模式，后续根据实际需要添加
    path('profile/', views.profile, name='profile'),
]
