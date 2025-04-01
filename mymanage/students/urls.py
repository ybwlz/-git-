from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    # 学生个人主页
    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    
    # 今日练琴
    path('practice/', views.practice, name='practice'),
    path('practice/check-in/', views.check_in, name='check_in'),
    path('practice/check-out/', views.check_out, name='check_out'),
    path('practice/scan-qrcode/', views.scan_qrcode, name='scan_qrcode'),
    path('practice/status/', views.practice_status, name='practice_status'),
    
    # 考勤记录
    path('attendance/', views.attendance, name='attendance'),
    path('attendance/history/', views.attendance_history, name='attendance_history'),
    path('attendance/stats/', views.attendance_stats, name='attendance_stats'),
    path('attendance/calendar-data/', views.attendance_calendar_data, name='attendance_calendar_data'),
    
    # 在线曲谱
    path('sheet-music/', views.sheet_music, name='sheet_music'),
    path('sheet-music/<int:sheet_id>/', views.sheet_music_detail, name='sheet_music_detail'),
    path('sheet-music/<int:sheet_id>/api/', views.sheet_music_detail_api, name='sheet_music_detail_api'),
    path('sheet-music/favorite/<int:sheet_music_id>/', views.toggle_favorite, name='toggle_favorite'),
]
