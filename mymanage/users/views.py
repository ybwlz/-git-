from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from .models import User
from .forms import UserRegistrationForm, UserLoginForm, UserPasswordResetForm
from mymanage.teachers.models import TeacherProfile
from mymanage.students.models import Student


def login_view(request):
    """用户登录视图"""
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user_type = form.cleaned_data.get('user_type')
            remember_me = form.cleaned_data.get('remember_me')
            
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                # 检查用户类型是否匹配
                if (user_type == 'student' and user.is_student) or \
                   (user_type == 'teacher' and user.is_teacher) or \
                   (user_type == 'admin' and (user.is_superuser or user.is_admin_user)):
                    login(request, user)
                    
                    # 设置会话过期时间
                    if not remember_me:
                        request.session.set_expiry(0)  # 浏览器关闭后会话过期
                    
                    # 根据用户类型重定向到不同的页面
                    if user.is_student:
                        return redirect('students:profile')
                    elif user.is_teacher:
                        return redirect('teachers:dashboard')
                    elif user.is_superuser or user.is_admin_user:
                        return redirect('admin:index')
                else:
                    messages.error(request, '用户类型不匹配，请选择正确的用户类型')
            else:
                messages.error(request, '用户名或密码错误')
    else:
        form = UserLoginForm()
    
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    """用户退出视图"""
    logout(request)
    messages.success(request, '您已成功退出登录')
    return redirect('login')


def register_view(request):
    """用户注册视图"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # 创建用户但不保存
            user = form.save(commit=False)
            # 设置用户类型
            user_type = form.cleaned_data.get('user_type')
            user.user_type = user_type
            # 保存用户
            user.save()
            
            # 根据用户类型创建相应的个人资料
            if user_type == 'teacher':
                # 创建教师个人资料
                TeacherProfile.objects.create(
                    user=user,
                    name=user.username,  # 初始名称使用用户名
                )
            elif user_type == 'student':
                # 创建学生个人资料
                Student.objects.create(
                    user=user,
                    name=user.username,  # 初始名称使用用户名
                    level=1,  # 默认为1级
                    target_level=10,  # 默认目标级别为10级
                    phone='',  # 学生电话先空着
                    parent_name='',  # 家长姓名先留空
                    parent_phone='',  # 家长电话先留空
                    school=''  # 就读学校先留空
                )
            
            messages.success(request, '注册成功，请登录')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'register.html', {'form': form})


def password_reset_view(request):
    """密码重置视图"""
    if request.method == 'POST':
        form = UserPasswordResetForm(request.POST)
        if form.is_valid():
            # 获取表单中的邮箱
            email = form.cleaned_data.get('email')
            
            # 这里需要实现发送邮件的逻辑
            # 通常会调用Django内置的密码重置功能
            
            messages.success(request, '密码重置链接已发送到您的邮箱，请查收')
            return redirect('login')
    else:
        form = UserPasswordResetForm()
    
    return render(request, 'password_reset.html', {'form': form})
