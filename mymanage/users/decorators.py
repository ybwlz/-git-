from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied
from django.contrib import messages


def teacher_required(function):
    """检查用户是否为教师的装饰器"""
    def wrap(request, *args, **kwargs):
        if request.user.is_authenticated and hasattr(request.user, 'is_teacher') and request.user.is_teacher:
            return function(request, *args, **kwargs)
        messages.error(request, '您没有教师权限，无法访问此页面')
        return redirect('login')
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def admin_required(function):
    """检查用户是否为管理员的装饰器"""
    def wrap(request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.is_superuser or request.user.is_admin_user):
            return function(request, *args, **kwargs)
        messages.error(request, '您没有管理员权限，无法访问此页面')
        return redirect('login')
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap
