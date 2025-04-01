from django.urls import path
from . import views

urlpatterns = [
    # 仪表板
    path('', views.attendance_dashboard, name='attendance_dashboard'),
    
    # 考勤会话管理
    path('session/create/', views.create_session, name='create_attendance_session'),
    path('session/<int:session_id>/', views.session_detail, name='attendance_session_detail'),
    path('session/<int:session_id>/close/', views.close_session, name='close_attendance_session'),
    
    # 二维码扫描API
    path('api/scan-qrcode/', views.scan_qrcode, name='scan_qrcode'),
    
    # 学生考勤历史
    path('history/student/', views.student_attendance_history, name='student_attendance_history'),
    
    # 教师考勤统计
    path('stats/teacher/', views.teacher_attendance_stats, name='teacher_attendance_stats'),
]
