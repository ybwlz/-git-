from django import forms
from .models import TeacherProfile, PrivacySetting

class TeacherProfileForm(forms.ModelForm):
    """教师个人信息表单"""
    email = forms.EmailField(label='邮箱', widget=forms.EmailInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = TeacherProfile
        fields = ['name', 'gender', 'phone', 'avatar', 'bio', 'specialties']
        widgets = {
            'specialties': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 如果实例存在，则初始化email字段
        if self.instance and self.instance.user:
            self.fields['email'].initial = self.instance.user.email

class PrivacySettingForm(forms.ModelForm):
    """隐私设置表单"""
    class Meta:
        model = PrivacySetting
        fields = ['phone_visibility', 'email_visibility', 'bio_visibility']
        widgets = {
            'phone_visibility': forms.Select(attrs={'class': 'form-control'}),
            'email_visibility': forms.Select(attrs={'class': 'form-control'}),
            'bio_visibility': forms.Select(attrs={'class': 'form-control'}),
        }

class TeacherRegistrationForm(forms.Form):
    """教师注册表单"""
    username = forms.CharField(label='用户名', max_length=30, 
                              widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label='密码', 
                              widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    confirm_password = forms.CharField(label='确认密码', 
                                      widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label='电子邮箱', 
                            widget=forms.EmailInput(attrs={'class': 'form-control'}))
    name = forms.CharField(label='姓名', max_length=50, 
                          widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(label='手机号码', max_length=11, 
                           widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', '两次输入的密码不一致')
        
        return cleaned_data

class PasswordChangeForm(forms.Form):
    """修改密码表单"""
    old_password = forms.CharField(
        label='当前密码',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    new_password = forms.CharField(
        label='新密码',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    confirm_password = forms.CharField(
        label='确认新密码',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if new_password and confirm_password and new_password != confirm_password:
            self.add_error('confirm_password', '两次输入的密码不一致')
        
        return cleaned_data
