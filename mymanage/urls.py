"""mymanage URL Configuration"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from mymanage.users.views import login_view, logout_view

urlpatterns = [
    path('admin/', admin.site.urls),
    # 首页
    path('', TemplateView.as_view(template_name='index.html'), name='index'),
    # 登录和注销
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    # 应用URLs
    path('users/', include('mymanage.users.urls')),
    path('students/', include('mymanage.students.urls')),
    path('teachers/', include('mymanage.teachers.urls')),
    path('courses/', include('mymanage.courses.urls')),
    path('attendance/', include('mymanage.attendance.urls')),
    path('finance/', include('mymanage.finance.urls')),
    path('scores/', include('mymanage.scores.urls')),
]

# 添加媒体和静态文件的URL模式
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # 添加静态文件URL模式
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
