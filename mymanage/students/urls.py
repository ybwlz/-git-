from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    # 学生个人主页
    path('profile/', views.profile, name='profile'),
    path('settings/', views.update_profile, name='update_profile'),
    
    # 今日练琴
    path('practice/', views.practice, name='practice'),
    path('practice/check-in/', views.check_in, name='check_in'),
    path('practice/check-out/', views.check_out, name='check_out'),
    path('practice/scan-qrcode/', views.scan_qrcode, name='scan_qrcode'),
    path('practice/status/', views.check_practice_status, name='practice_status'),
    path('practice/start/', views.start_practice, name='start_practice'),
    path('practice/join-waiting/', views.join_waiting_queue, name='join_waiting_queue'),
    path('practice/cancel-waiting/', views.cancel_waiting, name='cancel_waiting'),
    path('practice/end/', views.end_practice, name='end_practice'),
    path('practice/check-status/', views.check_practice_status, name='check_practice_status'),
    path('practice/check-waiting-status/', views.check_waiting_status, name='check_waiting_status'),
    path('practice/piano/', views.piano_practice, name='piano_practice'),
    path('waiting/', views.waiting, name='waiting'),
    
    # 考勤记录
    path('attendance/', views.attendance, name='attendance'),
    path('attendance/detail/', views.attendance_detail, name='attendance_detail'),
    path('attendance/history/', views.attendance_history, name='attendance_history'),
    path('attendance/stats/', views.attendance_stats, name='attendance_stats'),
    path('attendance/calendar-data/', views.attendance_calendar_data, name='attendance_calendar_data'),
    
    # 在线曲谱
    path('sheet-music/', views.sheet_music, name='sheet_music'),
    path('sheet-music/<int:sheet_id>/', views.sheet_music_detail, name='sheet_music_detail'),
    path('sheet-music/<int:sheet_id>/api/', views.sheet_music_detail_api, name='sheet_music_detail_api'),
    path('sheet-music/favorite/<int:sheet_music_id>/', views.toggle_favorite, name='toggle_favorite'),
    path('check-practice-status/', views.check_practice_status, name='check_practice_status'),
    path('check-active-practice/', views.check_active_practice, name='check_active_practice'),
]
