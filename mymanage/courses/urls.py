from django.urls import path
from . import views
from django.forms import forms

app_name = 'courses'

urlpatterns = [
    # 课程管理
    path('list/', views.course_list, name='list'),
    path('detail/<int:pk>/', views.course_detail, name='detail'),
    path('create/', views.course_create, name='create'),
    path('update/<int:pk>/', views.course_update, name='update'),
    
    # 课程安排管理
    path('schedule/create/<int:course_id>/', views.course_schedule_create, name='schedule_create'),
    path('schedule/update/<int:pk>/', views.course_schedule_update, name='schedule_update'),
    
    # 课程报名管理
    path('enrollment/create/', views.enrollment_create, name='enrollment_create'),
    path('enrollment/create/<int:course_id>/', views.enrollment_create, name='enrollment_create_for_course'),
    path('enrollment/update/<int:pk>/', views.enrollment_update, name='enrollment_update'),
    path('my-courses/', views.my_courses, name='my_courses'),
    
    # 曲谱管理
    path('sheet-music/list/', views.sheet_music_list, name='sheet_music_list'),
    path('sheet-music/detail/<int:pk>/', views.sheet_music_detail, name='sheet_music_detail'),
    path('sheet-music/create/', views.sheet_music_create, name='sheet_music_create'),
    path('sheet-music/update/<int:pk>/', views.sheet_music_update, name='sheet_music_update'),
    
    # 钢琴管理
    path('piano/list/', views.piano_list, name='piano_list'),
    path('piano/update/<int:pk>/', views.piano_update, name='piano_update'),
    path('piano/initialize/', views.initialize_pianos, name='initialize_pianos'),
]
