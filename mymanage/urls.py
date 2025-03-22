"""mymanage URL Configuration"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    # 首页
    path('', TemplateView.as_view(template_name='index.html'), name='index'),
    # 登录页
    path('login/', TemplateView.as_view(template_name='login.html'), name='login'),
    # 应用URLs
    path('users/', include('mymanage.users.urls')),
    path('students/', include('mymanage.students.urls')),
    path('teachers/', include('mymanage.teachers.urls')),
    path('courses/', include('mymanage.courses.urls')),
    path('attendance/', include('mymanage.attendance.urls')),
    path('finance/', include('mymanage.finance.urls')),
    path('scores/', include('mymanage.scores.urls')),
]

# 添加媒体文件的URL模式
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
