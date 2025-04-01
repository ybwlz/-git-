from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    # 考勤仪表板
    path('', views.attendance_dashboard, name='dashboard'),
    
    # 创建考勤会话
    path('create/', views.create_session, name='create_session'),
    
    # 考勤会话详情
    path('session/<int:session_id>/', views.session_detail, name='session_detail'),
    
    # 关闭考勤会话
    path('session/<int:session_id>/close/', views.close_session, name='close_session'),
    
    # 二维码扫描
    path('scan/', views.scan_qrcode, name='scan_qrcode'),
    
    # 学生考勤历史
    path('student/history/', views.student_attendance_history, name='student_attendance_history'),
    
    # 教师考勤统计
    path('stats/teacher/', views.teacher_attendance_stats, name='teacher_attendance_stats'),
    
    # 添加新的URL
    path('generate-qrcode/', views.generate_qrcode, name='generate_qrcode'),
    path('end-session/', views.end_qrcode_session, name='end_qrcode_session'),
]
