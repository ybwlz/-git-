from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm
from .models import User


class UserRegistrationForm(UserCreationForm):
    """用户注册表单"""
    USER_TYPE_CHOICES = (
        ('student', '学生'),
        ('teacher', '教师'),
    )
    
    user_type = forms.ChoiceField(
        label='用户类型',
        choices=USER_TYPE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'role-selector'})
    )
    
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2', 'user_type']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '用户名'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget = forms.PasswordInput(attrs={
            'class': 'form-control', 
            'placeholder': '密码'
        })
        self.fields['password2'].widget = forms.PasswordInput(attrs={
            'class': 'form-control', 
            'placeholder': '确认密码'
        })
        # 添加帮助文本
        self.fields['password1'].help_text = '密码必须至少包含8个字符，且不能是纯数字'


class UserLoginForm(AuthenticationForm):
    """用户登录表单"""
    USER_TYPE_CHOICES = (
        ('admin', '管理员'),
        ('teacher', '教师'),
        ('student', '学生'),
    )
    
    user_type = forms.ChoiceField(
        label='用户类型',
        choices=USER_TYPE_CHOICES,
        initial='student',
        widget=forms.HiddenInput()
    )
    
    remember_me = forms.BooleanField(
        required=False, 
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = User
        fields = ['username', 'password', 'user_type', 'remember_me']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget = forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '用户名'
        })
        self.fields['password'].widget = forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '密码'
        })
        # 重写错误消息
        self.error_messages = {
            'invalid_login': '用户名或密码错误，请重试'
        }


class UserPasswordResetForm(PasswordResetForm):
    """用户密码重置表单"""
    email = forms.EmailField(
        label='电子邮箱',
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': '邮箱地址'
        })
    )
