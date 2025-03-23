from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect, reverse
from functools import wraps
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect


def admin_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    管理员权限装饰器，检查当前登录用户是否为管理员
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_active and u.user_type == 'admin',
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def teacher_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    教师权限装饰器，检查当前登录用户是否为教师
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_active and u.user_type == 'teacher',
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def student_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    学生权限装饰器，检查当前登录用户是否为学生
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_active and u.user_type == 'student',
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def role_required(allowed_roles=None):
    """
    角色权限控制装饰器，检查用户是否拥有允许的角色
    @param allowed_roles: 允许的角色列表，例如 ['admin', 'teacher']
    """
    if allowed_roles is None:
        allowed_roles = []
        
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return HttpResponseRedirect(reverse('login'))
                
            if request.user.user_type in allowed_roles:
                return view_func(request, *args, **kwargs)
            else:
                # 根据用户角色重定向到对应的主页
                if request.user.user_type == 'admin':
                    return HttpResponseRedirect(reverse('admin:dashboard'))
                elif request.user.user_type == 'teacher':
                    return HttpResponseRedirect(reverse('teachers:dashboard'))
                elif request.user.user_type == 'student':
                    return HttpResponseRedirect(reverse('students:dashboard'))
                    
                # 如果不是上述任何角色，则返回权限拒绝
                raise PermissionDenied
                
        return wrapper
    return decorator 