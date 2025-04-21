"""mymanage URL Configuration"""
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView, RedirectView
from mymanage.users import views as user_views
from mymanage.admin import mymanage_admin_site

urlpatterns = [
    # 管理后台
    path('admin/login/', RedirectView.as_view(url='/login/', permanent=False)),  # 重定向admin登录页面
    path('admin/', mymanage_admin_site.urls),
    
    # 用户认证
    path('login/', user_views.login_view, name='login'),
    path('logout/', user_views.logout_view, name='logout'),
    path('register/', user_views.register_view, name='register'),
    path('password-reset/', user_views.password_reset_view, name='password_reset'),
    
    # 应用模块
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('', include('mymanage.users.urls')),
    path('students/', include('mymanage.students.urls')),
    path('teachers/', include('mymanage.teachers.urls')),
    path('courses/', include('mymanage.courses.urls')),
    path('attendance/', include('mymanage.attendance.urls')),
    path('finance/', include('mymanage.finance.urls')),
]

# 开发环境下添加静态文件和媒体文件的访问URL
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
