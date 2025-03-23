from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import RegexValidator

from mymanage.users.models import User
from .models import Student, StudentNotes


class StudentForm(forms.ModelForm):
    """
    学生信息表单
    """
    phone_regex = RegexValidator(
        regex=r'^\d{11}$',
        message="手机号必须是11位数字"
    )
    
    parent_phone = forms.CharField(
        validators=[phone_regex],
        max_length=11,
        widget=forms.TextInput(attrs={'placeholder': '请输入11位手机号'})
    )
    
    birth_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    
    class Meta:
        model = Student
        fields = ['student_id', 'name', 'gender', 'birth_date', 'address', 'parent_name', 'parent_phone', 'is_active']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }


class UserCreationWithStudentForm(UserCreationForm):
    """
    创建学生用户的表单
    """
    student_id = forms.CharField(
        max_length=20,
        label='学号',
        widget=forms.TextInput(attrs={'placeholder': '请输入学生学号'})
    )
    
    name = forms.CharField(
        max_length=50,
        label='姓名',
        widget=forms.TextInput(attrs={'placeholder': '请输入学生姓名'})
    )
    
    gender = forms.ChoiceField(
        choices=Student.GENDER_CHOICES,
        label='性别'
    )
    
    parent_name = forms.CharField(
        max_length=50,
        label='家长姓名',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': '请输入家长姓名'})
    )
    
    parent_phone = forms.CharField(
        max_length=11,
        label='家长电话',
        widget=forms.TextInput(attrs={'placeholder': '请输入家长手机号'})
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'student_id', 'name', 'gender', 'parent_name', 'parent_phone']
    
    def save(self, commit=True):
        # 创建用户
        user = super().save(commit=False)
        user.user_type = 'student'
        
        if commit:
            user.save()
            
            # 创建关联的学生资料
            Student.objects.create(
                user=user,
                student_id=self.cleaned_data['student_id'],
                name=self.cleaned_data['name'],
                gender=self.cleaned_data['gender'],
                parent_name=self.cleaned_data['parent_name'],
                parent_phone=self.cleaned_data['parent_phone']
            )
        
        return user


class StudentBulkImportForm(forms.Form):
    """
    批量导入学生的表单
    """
    file = forms.FileField(
        label='Excel文件',
        help_text='请上传包含学生信息的Excel文件，格式：学号、姓名、性别、出生日期(可选)、家长姓名、家长电话'
    )


class StudentNotesForm(forms.ModelForm):
    """
    学生笔记表单
    """
    class Meta:
        model = StudentNotes
        fields = ['title', 'content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 5}),
        }


class StudentSearchForm(forms.Form):
    """
    学生搜索表单
    """
    keyword = forms.CharField(
        label='关键词',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': '输入学号、姓名或家长姓名'})
    )
    
    gender = forms.ChoiceField(
        label='性别',
        choices=[('', '所有')] + list(Student.GENDER_CHOICES),
        required=False
    )
    
    is_active = forms.ChoiceField(
        label='状态',
        choices=[('', '所有'), ('1', '活跃'), ('0', '不活跃')],
        required=False
    )
    
    join_date_start = forms.DateField(
        label='入学日期从',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    
    join_date_end = forms.DateField(
        label='入学日期至',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
