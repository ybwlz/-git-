from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    # 学生列表和详情
    path('list/', views.student_list, name='list'),
    path('detail/<int:pk>/', views.student_detail, name='detail'),
    
    # 学生账户创建和编辑
    path('create/', views.student_create, name='create'),
    path('edit/<int:pk>/', views.student_edit, name='edit'),
    
    # 学生笔记管理
    path('detail/<int:student_pk>/delete-note/<int:note_pk>/', 
         views.student_delete_note, name='delete_note'),
    
    # 学生个人资料
    path('profile/', views.student_profile, name='profile'),
    
    # 学生练习页面
    path('practice/', views.student_practice, name='practice'),
    
    # 学生考勤记录
    path('exam/', views.student_exam, name='exam'),
    
    # 学生成绩/曲谱
    path('grades/', views.student_grades, name='grades'),
    
    # 批量导入学生
    path('bulk-import/', views.student_bulk_import, name='bulk_import'),
]
