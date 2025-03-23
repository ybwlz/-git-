from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    # 考勤记录主页
    path('record/', views.record_attendance, name='record'),
    
    # 考勤会话详情
    path('session/<int:pk>/', views.session_detail, name='session_detail'),
    
    # 二维码生成和详情
    path('qrcode/<int:course_id>/', views.generate_qrcode, name='qrcode'),
    path('qrcode/detail/<int:pk>/', views.qrcode_detail, name='qrcode_detail'),
    
    # 学生签到签退API
    path('check-in/', views.student_check_in, name='check_in'),
    path('check-out/', views.student_check_out, name='check_out'),
    
    # 考勤统计
    path('statistics/', views.attendance_statistics, name='statistics'),
]
