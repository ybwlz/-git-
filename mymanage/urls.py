"""mymanage URL Configuration"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from mymanage.users import views as user_views

urlpatterns = [
    # 管理后台
    path('admin/', admin.site.urls),
    
    # 用户认证
    path('login/', user_views.login_view, name='login'),
    path('logout/', user_views.logout_view, name='logout'),
    path('register/', user_views.register_view, name='register'),
    path('password-reset/', user_views.password_reset_view, name='password_reset'),
    
    # 应用模块
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('teachers/', include('mymanage.teachers.urls')),
    path('students/', include('mymanage.students.urls')),
    path('courses/', include('mymanage.courses.urls')),
    path('attendance/', include('mymanage.attendance.urls')),
    path('finance/', include('mymanage.finance.urls')),
]

# 在开发环境中提供媒体文件支持
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
