from django.urls import path
from . import views

app_name = 'scores'

urlpatterns = [
    # 考试相关URL
    path('exam/list/', views.exam_list, name='exam_list'),
    path('exam/create/', views.exam_create, name='exam_create'),
    path('exam/edit/<int:pk>/', views.exam_edit, name='exam_edit'),
    path('exam/detail/<int:pk>/', views.exam_detail, name='exam_detail'),
    
    # 成绩相关URL
    path('list/', views.score_list, name='score_list'),
    path('create/', views.score_create, name='score_create'),
    path('create/<int:exam_id>/', views.score_create, name='score_create_for_exam'),
    path('edit/<int:pk>/', views.score_edit, name='score_edit'),
    path('detail/<int:pk>/', views.score_detail, name='score_detail'),
    path('batch/<int:exam_id>/', views.batch_score_create, name='batch_score_create'),
    
    # 统计相关URL
    path('statistics/', views.statistics, name='statistics'),
    path('student/<int:student_id>/', views.student_scores, name='student_scores'),
    path('export/<int:exam_id>/', views.export_scores, name='export_scores'),
    
    # AJAX请求
    path('ajax/performance-level/', views.ajax_get_performance_level, name='ajax_performance_level'),
]
