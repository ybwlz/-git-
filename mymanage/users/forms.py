from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm, SetPasswordForm, PasswordChangeForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import User


class CustomAuthenticationForm(AuthenticationForm):
    """自定义登录表单"""
    username = forms.CharField(
        label=_("用户名"),
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入用户名'})
    )
    password = forms.CharField(
        label=_("密码"),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '请输入密码'})
    )
    user_type = forms.ChoiceField(
        label=_("用户类型"),
        choices=User.USER_TYPE_CHOICES,
        widget=forms.RadioSelect(),
        required=True
    )
    remember_me = forms.BooleanField(
        label=_("记住我"), 
        required=False, 
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class CustomUserCreationForm(UserCreationForm):
    """用户注册表单"""
    email = forms.EmailField(required=True, help_text='必填，请输入有效的电子邮箱地址')
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'user_type']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': '用户名'
        })
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': '电子邮箱'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': '密码'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': '确认密码'
        })
        self.fields['user_type'].widget.attrs.update({
            'class': 'form-select'
        })


class UserRegistrationForm(UserCreationForm):
    """用户注册表单"""
    username = forms.CharField(
        label=_("用户名"),
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入用户名'})
    )
    password1 = forms.CharField(
        label=_("密码"),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '请输入密码'})
    )
    password2 = forms.CharField(
        label=_("确认密码"),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '请再次输入密码'})
    )
    user_type = forms.ChoiceField(
        label=_("用户类型"),
        choices=User.USER_TYPE_CHOICES,
        widget=forms.RadioSelect(),
        required=True
    )
    
    class Meta:
        model = User
        fields = ('username', 'password1', 'password2', 'user_type')


class UserProfileForm(forms.ModelForm):
    """用户个人资料表单"""
    username = forms.CharField(
        label=_("用户名"),
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': True})
    )
    email = forms.EmailField(
        label=_("邮箱"),
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    phone = forms.CharField(
        label=_("手机号码"),
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=False
    )
    avatar = forms.ImageField(
        label=_("头像"),
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        required=False
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'phone', 'avatar')
    
    def clean_phone(self):
        """验证手机号码格式"""
        phone = self.cleaned_data.get('phone')
        if phone and not phone.isdigit():
            raise ValidationError(_("手机号码必须是数字"))
        if phone and len(phone) != 11:
            raise ValidationError(_("手机号码必须是11位"))
        return phone


class ResetPasswordForm(forms.Form):
    """重置密码表单"""
    old_password = forms.CharField(
        label=_("原密码"),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '请输入原密码'})
    )
    new_password1 = forms.CharField(
        label=_("新密码"),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '请输入新密码'})
    )
    new_password2 = forms.CharField(
        label=_("确认新密码"),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '请再次输入新密码'})
    )
    
    def clean_new_password2(self):
        """验证两次输入的密码是否一致"""
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2 and password1 != password2:
            raise ValidationError(_("两次输入的密码不一致"))
        return password2


class CustomPasswordResetForm(PasswordResetForm):
    """密码重置表单"""
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': '电子邮箱'
    }))


class CustomSetPasswordForm(SetPasswordForm):
    """设置新密码表单"""
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '新密码'
        })
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '确认新密码'
        })
    )


class ProfileForm(forms.ModelForm):
    """用户资料编辑表单"""
    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'avatar']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
        })
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
        })
        self.fields['phone'].widget.attrs.update({
            'class': 'form-control',
        })
        self.fields['avatar'].widget.attrs.update({
            'class': 'form-control',
        })
        
    def clean_email(self):
        email = self.cleaned_data.get('email')
        username = self.cleaned_data.get('username')
        # 检查是否有其他用户已经使用了这个电子邮箱
        if email and User.objects.filter(email=email).exclude(username=username).exists():
            raise forms.ValidationError('该电子邮箱已被其他用户使用')
        return email


class CustomPasswordChangeForm(PasswordChangeForm):
    """用户修改密码表单"""
    old_password = forms.CharField(
        label="旧密码",
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '当前密码',
            'autocomplete': 'current-password',
        }),
    )
    new_password1 = forms.CharField(
        label="新密码",
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '新密码',
            'autocomplete': 'new-password',
        }),
    )
    new_password2 = forms.CharField(
        label="确认新密码",
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '确认新密码',
            'autocomplete': 'new-password',
        }),
    )
