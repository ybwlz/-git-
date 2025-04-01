from django.urls import path
from . import views

app_name = 'teachers'

urlpatterns = [
    # 仪表板
    path('dashboard/', views.teacher_dashboard, name='dashboard'),
    
    # 个人资料
    path('profile/', views.teacher_profile, name='profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    
    # 学生管理
    path('students/', views.teacher_students, name='students'),
    path('students/<int:student_id>/', views.student_detail, name='student_detail'),
    path('students/add/', views.add_student, name='add_student'),
    path('students/<int:student_id>/edit/', views.edit_student, name='edit_student'),
    path('students/<int:student_id>/delete/', views.delete_student, name='delete_student'),
    
    # 课程管理
    path('courses/', views.teacher_courses, name='courses'),
    path('courses/<int:course_id>/', views.course_detail, name='course_detail'),
    path('courses/add/', views.add_course, name='add_course'),
    path('courses/<int:course_id>/edit/', views.edit_course, name='edit_course'),
    
    # 考勤管理
    path('attendance/', views.teacher_attendance, name='attendance'),
    path('attendance/qrcode/', views.generate_qrcode, name='generate_qrcode'),
    path('attendance/qrcode/<uuid:qrcode_id>/', views.show_qrcode, name='show_qrcode'),
    path('attendance/session/<int:session_id>/', views.attendance_session_detail, name='session_detail'),
    path('attendance/stats/', views.attendance_stats, name='attendance_stats'),
    
    # 曲谱管理
    path('sheet-music/', views.teacher_sheet_music, name='sheet_music'),
    path('sheet-music/<int:sheet_id>/', views.sheet_music_detail, name='sheet_music_detail'),
    path('sheet-music/add/', views.add_sheet_music, name='add_sheet_music'),
    path('sheet-music/<int:sheet_id>/edit/', views.edit_sheet_music, name='edit_sheet_music'),
    path('sheet-music/<int:sheet_id>/delete/', views.delete_sheet_music, name='delete_sheet_music'),
    
    # 财务管理
    path('finance/', views.teacher_finance, name='finance'),
    path('finance/payments/', views.teacher_payments, name='payments'),
]
