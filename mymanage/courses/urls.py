from django.urls import path
from . import views

urlpatterns = [
    # 钢琴管理
    path('pianos/', views.piano_list, name='piano_list'),
    path('pianos/<int:piano_id>/', views.piano_detail, name='piano_detail'),
    path('pianos/manage/', views.piano_manage, name='piano_create'),
    path('pianos/manage/<int:piano_id>/', views.piano_manage, name='piano_edit'),
    
    # 曲谱管理
    path('sheet-music/', views.sheet_music_list, name='sheet_music_list'),
    path('sheet-music/<int:sheet_id>/', views.sheet_music_detail, name='sheet_music_detail'),
    path('sheet-music/manage/', views.sheet_music_manage, name='sheet_music_create'),
    path('sheet-music/manage/<int:sheet_id>/', views.sheet_music_manage, name='sheet_music_edit'),
    path('sheet-music/delete/<int:sheet_id>/', views.delete_sheet_music, name='sheet_music_delete'),
    
    # 自动排课与练习队列API
    path('api/scheduler/status/', views.auto_scheduler_status, name='auto_scheduler_status'),
    path('api/scheduler/join-queue/', views.join_practice_queue, name='join_practice_queue'),
    path('api/scheduler/check-out/', views.check_out, name='check_out'),
]
