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
    path('students/ajax/<int:student_id>/', views.student_detail_ajax, name='student_detail_ajax'),
    path('students/add/', views.add_student, name='add_student'),
    path('students/<int:student_id>/edit/', views.edit_student, name='edit_student'),
    path('students/<int:student_id>/delete/', views.delete_student, name='delete_student'),
    
    # 练琴安排（替代课程管理）
    path('piano-arrangement/', views.piano_arrangement, name='piano_arrangement'),
    path('piano-arrangement/refresh/', views.refresh_piano_status, name='refresh_piano_status'),
    path('piano-arrangement/assign/', views.assign_piano, name='assign_piano'),
    path('piano-arrangement/force-checkout/', views.force_checkout, name='force_checkout'),
    path('piano-arrangement/maintenance/', views.piano_maintenance, name='piano_maintenance'),
    path('piano-arrangement/activate/', views.activate_piano, name='activate_piano'),
    path('piano-arrangement/remove-from-queue/', views.remove_from_queue, name='remove_from_queue'),
    
    # 考勤管理
    path('attendance/', views.teacher_attendance, name='attendance'),
    path('attendance/qrcode/', views.generate_qrcode, name='generate_qrcode'),
    path('attendance/qrcode/ajax/', views.generate_qrcode_ajax, name='generate_qrcode_ajax'),
    path('attendance/session/<int:session_id>/', views.attendance_session_detail, name='session_detail'),
    path('attendance/manual-checkin/', views.manual_checkin, name='manual_checkin'),
    path('attendance/checkout/', views.attendance_checkout, name='attendance_checkout'),
    path('attendance/end-session/', views.end_session, name='end_session'),
    
    # 曲谱管理
    path('sheet-music/', views.teacher_sheet_music, name='sheet_music'),
    path('sheet-music/<int:sheet_id>/', views.sheet_music_detail, name='sheet_music_detail'),
    path('sheet-music/add/', views.add_sheet_music, name='add_sheet_music'),
    path('sheet-music/<int:sheet_id>/edit/', views.edit_sheet_music, name='edit_sheet_music'),
    path('sheet-music/<int:sheet_id>/delete/', views.delete_sheet_music, name='delete_sheet_music'),
    
    # 财务管理
    path('finance/', views.teacher_finance, name='finance'),
    path('finance/payments/', views.teacher_payments, name='payments'),
    
    # API接口
    path('api/students/', views.get_students_api, name='get_students_api'),
    path('api/payment-categories/', views.get_payment_categories_api, name='get_payment_categories_api'),
    path('api/payments/add/', views.add_payment_api, name='add_payment_api'),
    path('api/payments/<int:payment_id>/mark-as-paid/', views.mark_payment_as_paid_api, name='mark_payment_as_paid_api'),
    path('api/payments/stats/', views.get_payment_stats_api, name='get_payment_stats_api'),
]
