from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.urls import reverse, reverse_lazy
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.tokens import default_token_generator
from django.views.generic.edit import FormView
from django.contrib.auth.views import (
    LoginView, LogoutView, PasswordResetView, 
    PasswordResetDoneView, PasswordResetConfirmView, 
    PasswordResetCompleteView, PasswordChangeView
)

from .models import User
from .forms import (
    CustomAuthenticationForm, UserRegistrationForm, 
    UserProfileForm, ResetPasswordForm,
    ProfileForm, CustomPasswordChangeForm
)


class UserAuthView:
    """用户认证视图类"""
    
    @staticmethod
    def login_view(request):
        """用户登录视图"""
        # 添加调试信息
        print(f"认证状态: {request.user.is_authenticated}")
        if request.user.is_authenticated:
            print(f"用户类型: {request.user.user_type}")
            
            # 根据用户类型重定向到对应的页面
            if request.user.user_type == 'admin':
                return redirect('/admin/')  # 直接重定向到Django管理界面
            elif request.user.user_type == 'teacher':
                return redirect('teachers:dashboard')  # 使用教师仪表盘
            elif request.user.user_type == 'student':
                return redirect('students:profile')
                    
        if request.method == 'POST':
            form = CustomAuthenticationForm(data=request.POST)
            if form.is_valid():
                username = form.cleaned_data.get('username')
                password = form.cleaned_data.get('password')
                user_type = form.cleaned_data.get('user_type')
                remember_me = form.cleaned_data.get('remember_me', False)
                
                # 认证用户
                user = authenticate(username=username, password=password)
                
                if user is not None and user.user_type == user_type:
                    # 设置session过期时间
                    if not remember_me:
                        request.session.set_expiry(0)  # 浏览器关闭即过期
                    else:
                        # 设置为30天
                        request.session.set_expiry(30 * 24 * 60 * 60)
                    
                    login(request, user)
                    messages.success(request, f'欢迎回来，{username}！')
                    
                    # 根据用户类型重定向到对应的页面
                    if user.user_type == 'admin':
                        return redirect('/admin/')  # 直接重定向到Django管理界面
                    elif user.user_type == 'teacher':
                        return redirect('teachers:dashboard')  # 使用教师仪表盘
                    elif user.user_type == 'student':
                        return redirect('students:profile')
                else:
                    messages.error(request, '用户名或密码错误，或者选择的用户类型不匹配！')
            else:
                messages.error(request, '登录表单验证失败，请检查输入！')
        else:
            # 需要显式登出，确保用户状态干净
            logout(request)
            form = CustomAuthenticationForm()
            
        context = {
            'form': form
        }
        
        return render(request, 'login.html', context)
    
    @staticmethod
    def register_view(request):
        """用户注册视图"""
        if request.user.is_authenticated:
            return redirect('users:profile')
            
        if request.method == 'POST':
            form = UserRegistrationForm(request.POST)
            if form.is_valid():
                user = form.save()
                messages.success(request, '注册成功！请使用您的凭据登录。')
                return redirect('users:login')
            else:
                messages.error(request, '注册失败，请检查表单错误！')
        else:
            form = UserRegistrationForm()
            
        context = {
            'form': form
        }
        return render(request, 'register.html', context)
    
    @staticmethod
    def logout_view(request):
        """用户登出视图"""
        logout(request)
        messages.info(request, '您已成功登出！')
        return redirect('login')


class UserProfileView:
    """用户个人资料视图类"""
    
    @staticmethod
    @login_required
    def profile_view(request):
        """用户个人资料视图"""
        if request.method == 'POST':
            form = ProfileForm(request.POST, request.FILES, instance=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, '个人资料已成功更新！')
                return redirect('users:profile')
        else:
            form = ProfileForm(instance=request.user)
            
        return render(request, 'users/profile.html', {
            'form': form
        })
    
    @staticmethod
    @login_required
    def change_password(request):
        """修改密码视图"""
        if request.method == 'POST':
            form = CustomPasswordChangeForm(request.user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, '密码已成功更新！')
                return redirect('users:profile')
            else:
                messages.error(request, '密码修改失败，请检查表单错误！')
        else:
            form = CustomPasswordChangeForm(request.user)
            
        return render(request, 'users/change_password.html', {
            'form': form
        })


class PasswordResetView:
    """密码重置视图类"""
    
    @staticmethod
    def password_reset_request(request):
        """密码重置请求视图"""
        if request.method == 'POST':
            email = request.POST.get('email', '')
            if not email:
                messages.error(request, '请输入邮箱地址！')
                return redirect('users:password_reset_request')
                
            # 检查邮箱是否存在
            try:
                user = User.objects.get(email=email)
                # 生成密码重置链接
                current_site = get_current_site(request)
                mail_subject = '重置您的密码'
                message = render_to_string('users/password_reset_email.html', {
                    'user': user,
                    'domain': current_site.domain,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': default_token_generator.make_token(user),
                })
                email_message = EmailMessage(mail_subject, message, to=[email])
                email_message.send()
                
                messages.success(request, '重置密码的邮件已发送到您的邮箱，请查收并按照指引操作。')
                return redirect('users:login')
            except User.DoesNotExist:
                messages.error(request, '该邮箱地址不存在！')
                return redirect('users:password_reset_request')
                
        return render(request, 'users/password_reset_request.html')
    
    @staticmethod
    def password_reset_confirm(request, uidb64, token):
        """密码重置确认视图"""
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
            
        # 检查用户和token是否有效
        if user is not None and default_token_generator.check_token(user, token):
            if request.method == 'POST':
                password1 = request.POST.get('password1', '')
                password2 = request.POST.get('password2', '')
                
                if not password1 or not password2:
                    messages.error(request, '请输入新密码！')
                    return redirect('users:password_reset_confirm', uidb64=uidb64, token=token)
                    
                if password1 != password2:
                    messages.error(request, '两次输入的密码不一致！')
                    return redirect('users:password_reset_confirm', uidb64=uidb64, token=token)
                    
                # 更新密码
                user.set_password(password1)
                user.save()
                
                messages.success(request, '密码已成功重置！请使用新密码登录。')
                return redirect('users:login')
            
            return render(request, 'users/password_reset_confirm.html')
        else:
            messages.error(request, '密码重置链接无效！可能已过期或已使用。')
            return redirect('users:password_reset_request')


class CustomPasswordResetView(PasswordResetView):
    """自定义密码重置视图"""
    template_name = 'users/password_reset_form.html'
    email_template_name = 'users/password_reset_email.html'
    subject_template_name = 'users/password_reset_subject.txt'
    success_url = reverse_lazy('users:password_reset_done')

class CustomPasswordResetDoneView(PasswordResetDoneView):
    """自定义密码重置完成视图"""
    template_name = 'users/password_reset_done.html'

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """自定义密码重置确认视图"""
    template_name = 'users/password_reset_confirm.html'
    success_url = reverse_lazy('users:password_reset_complete')

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    """自定义密码重置完成视图"""
    template_name = 'users/password_reset_complete.html'


# 实例化视图函数
login_view = UserAuthView.login_view
register_view = UserAuthView.register_view
logout_view = UserAuthView.logout_view
profile_view = UserProfileView.profile_view
change_password = UserProfileView.change_password
password_reset_request = PasswordResetView.password_reset_request
password_reset_confirm = PasswordResetView.password_reset_confirm
