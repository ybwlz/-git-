from django.urls import path
from . import views

app_name = 'teachers'

urlpatterns = [
    # 教师仪表板
    path('dashboard/', views.teacher_dashboard, name='dashboard'),
    
    # 教师个人资料
    path('profile/', views.teacher_profile, name='profile'),
    path('certificate/add/', views.add_certificate, name='add_certificate'),
    
    # 学生管理
    path('students/', views.student_list, name='student_list'),
    path('students/<int:student_id>/', views.student_detail, name='student_detail'),
    
    # 考勤管理
    path('attendance/', views.attendance_management, name='attendance_management'),
    path('attendance/qrcode/<int:schedule_id>/', views.generate_qrcode, name='generate_qrcode'),
    path('attendance/record/', views.attendance_record, name='attendance_record'),
    path('attendance/record/<int:course_id>/', views.attendance_record, name='course_attendance_record'),
    
    # 财务管理
    path('finance/', views.finance_management, name='finance_management'),
    
    # 曲谱管理
    path('sheet-music/', views.sheet_music_management, name='sheet_music_management'),
    
    # 课程管理
    path('courses/', views.course_list, name='course_list'),
    path('courses/<int:course_id>/', views.course_detail, name='course_detail'),
]
