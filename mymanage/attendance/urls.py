from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    # 示例URL模式，后续根据实际需要添加
    path('record/', views.record_attendance, name='record'),
    path('qrcode/<int:course_id>/', views.generate_qrcode, name='qrcode'),
]
