from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from .models import User
from .forms import UserRegistrationForm, UserLoginForm, UserPasswordResetForm
from mymanage.teachers.models import TeacherProfile
from mymanage.teachers.forms import TeacherProfileForm
from mymanage.students.models import Student
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.contrib.auth.forms import PasswordResetForm
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
import random
import string
from django.core.cache import cache
from django.http import JsonResponse


def generate_verification_code():
    """生成6位数字验证码"""
    return ''.join(random.choices(string.digits, k=6))


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
                messages.error(request, '用户名或密码错误，请重试')
        else:
            # 处理表单验证错误
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{error}')
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
        username = request.POST.get('username')
        email = request.POST.get('email')
        
        try:
            # 先查找用户是否存在
            user = User.objects.get(username=username)
            
            # 检查用户是否绑定了邮箱
            if not user.email:
                messages.error(request, '该用户未绑定邮箱，无法使用密码重置功能。请联系管理员重置密码。')
                return render(request, 'password_reset.html')
            
            # 验证邮箱是否匹配
            if user.email != email:
                messages.error(request, '用户名和邮箱不匹配，请检查输入是否正确。')
                return render(request, 'password_reset.html')
            
            # 生成验证码
            verification_code = generate_verification_code()
            
            # 将验证码存入缓存，设置5分钟过期
            cache_key = f'reset_code_{user.id}'
            cache.set(cache_key, verification_code, 300)  # 5分钟过期
            
            # 发送验证码邮件
            subject = '苗韵琴行 - 密码重置验证码'
            message = f"""
            尊敬的 {user.username}：
            
            您的密码重置验证码是：{verification_code}
            验证码有效期为5分钟。
            
            如果这不是您本人的操作，请忽略此邮件。
            
            © 2023 苗韵琴行. 保留所有权利.
            """
            
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )
            
            # 将用户ID存入session，用于后续验证
            request.session['reset_user_id'] = user.id
            
            messages.success(request, '验证码已发送到您的邮箱，请查收。')
            return redirect('users:password_reset_verify')
            
        except User.DoesNotExist:
            messages.error(request, '用户名不存在，请检查输入是否正确。')
    
    return render(request, 'password_reset.html')


def password_reset_verify_view(request):
    """验证码验证视图"""
    user_id = request.session.get('reset_user_id')
    if not user_id:
        messages.error(request, '请先申请密码重置。')
        return redirect('users:password_reset')
    
    if request.method == 'POST':
        verification_code = request.POST.get('verification_code')
        cache_key = f'reset_code_{user_id}'
        stored_code = cache.get(cache_key)
        
        if stored_code and verification_code == stored_code:
            # 验证码正确，清除缓存
            cache.delete(cache_key)
            # 生成重置令牌
            user = User.objects.get(pk=user_id)
            token = default_token_generator.make_token(user)
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            # 重定向到密码重置确认页面
            return redirect('users:password_reset_confirm', uidb64=uidb64, token=token)
        else:
            messages.error(request, '验证码错误或已过期，请重新申请。')
            return redirect('users:password_reset')
    
    return render(request, 'password_reset_verify.html')


def password_reset_confirm_view(request, uidb64, token):
    """密码重置确认视图"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        
        if default_token_generator.check_token(user, token):
            if request.method == 'POST':
                new_password1 = request.POST.get('new_password1')
                new_password2 = request.POST.get('new_password2')
                
                if new_password1 and new_password2:
                    if new_password1 == new_password2:
                        # 验证密码强度
                        if len(new_password1) < 8:
                            messages.error(request, '密码长度至少需要8位')
                            return render(request, 'password_reset_confirm.html')
                        
                        if not any(c.isdigit() for c in new_password1) or not any(c.isalpha() for c in new_password1):
                            messages.error(request, '密码必须包含字母和数字')
                            return render(request, 'password_reset_confirm.html')
                        
                        # 设置新密码
                        user.set_password(new_password1)
                        user.save()
                        messages.success(request, '密码已成功重置，请使用新密码登录。')
                        return redirect('users:user_login')
                    else:
                        messages.error(request, '两次输入的密码不一致')
                else:
                    messages.error(request, '请填写所有必填字段')
            
            return render(request, 'password_reset_confirm.html')
        else:
            messages.error(request, '重置链接已失效，请重新申请。')
            return redirect('users:password_reset')
            
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        messages.error(request, '重置链接无效，请重新申请。')
        return redirect('users:password_reset')


class CustomPasswordResetView(PasswordResetView):
    template_name = 'password_reset.html'
    email_template_name = 'password_reset_email.html'
    subject_template_name = 'password_reset_subject.txt'
    form_class = PasswordResetForm
    
    def form_valid(self, form):
        username = form.cleaned_data.get('username')
        email = form.cleaned_data.get('email')
        
        try:
            # 先查找用户是否存在
            user = User.objects.get(username=username)
            
            # 检查用户是否绑定了邮箱
            if not user.email:
                messages.error(self.request, '该用户未绑定邮箱，无法使用密码重置功能。请联系管理员重置密码。')
                return self.form_invalid(form)
            
            # 验证邮箱是否匹配
            if user.email != email:
                messages.error(self.request, '用户名和邮箱不匹配，请检查输入是否正确。')
                return self.form_invalid(form)
            
            # 生成重置链接
            context = {
                'user': user,
                'protocol': 'http',
                'domain': self.request.get_host(),
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            }
            
            # 渲染邮件内容
            subject = render_to_string(self.subject_template_name, context)
            subject = ''.join(subject.splitlines())
            html_message = render_to_string(self.email_template_name, context)
            plain_message = strip_tags(html_message)
            
            # 发送邮件
            send_mail(
                subject,
                plain_message,
                settings.EMAIL_HOST_USER,
                [email],
                html_message=html_message,
                fail_silently=False,
            )
            messages.success(self.request, '密码重置链接已发送到您的邮箱，请查收。')
            return super().form_valid(form)
        except User.DoesNotExist:
            messages.error(self.request, '用户名不存在，请检查输入是否正确。')
            return self.form_invalid(form)


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'password_reset_confirm.html'


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'password_reset_complete.html'


@login_required
def update_profile_ajax(request):
    """AJAX更新个人信息"""
    if request.method == 'POST':
        teacher_profile = request.user.teacher_profile
        form = TeacherProfileForm(request.POST, request.FILES, instance=teacher_profile)
        if form.is_valid():
            form.save()
            
            # 处理邮箱更新
            email = request.POST.get('email')
            if email and email != request.user.email:
                request.user.email = email
                request.user.save(update_fields=['email'])
                
            return JsonResponse({'status': 'success', 'message': '更新成功'})
        return JsonResponse({'status': 'error', 'message': '表单验证失败'})
    return JsonResponse({'status': 'error', 'message': '不支持的请求方法'})
