from django import forms
from .models import Teacher, TeacherCertificate
from django.contrib.auth.forms import UserCreationForm
from mymanage.users.models import User


class TeacherProfileForm(forms.ModelForm):
    """教师个人信息表单"""
    class Meta:
        model = Teacher
        fields = ['name', 'gender', 'birth_date', 'phone', 'address', 
                 'email', 'specialty']
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
        }


class TeacherCertificateForm(forms.ModelForm):
    """教师证书表单"""
    class Meta:
        model = TeacherCertificate
        fields = ['certificate_name', 'certificate_number', 'issue_date', 
                 'issue_organization', 'certificate_image']
        widgets = {
            'issue_date': forms.DateInput(attrs={'type': 'date'}),
        }


class TeacherRegistrationForm(UserCreationForm):
    """教师注册表单"""
    teacher_id = forms.CharField(max_length=20, label='教师工号')
    name = forms.CharField(max_length=50, label='姓名')
    phone = forms.CharField(max_length=11, label='电话')
    specialty = forms.CharField(max_length=100, label='专业特长', required=False)
    
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2', 'email']
        
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'teacher'
        if commit:
            user.save()
            Teacher.objects.create(
                user=user,
                teacher_id=self.cleaned_data.get('teacher_id'),
                name=self.cleaned_data.get('name'),
                phone=self.cleaned_data.get('phone'),
                email=self.cleaned_data.get('email', ''),
                specialty=self.cleaned_data.get('specialty', '')
            )
        return user
