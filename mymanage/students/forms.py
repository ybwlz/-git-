from django import forms
from .models import Student, PracticeRecord, Attendance, SheetMusic, StudentFavorite

class StudentProfileForm(forms.ModelForm):
    """学生个人信息表单"""
    class Meta:
        model = Student
        fields = ['name', 'level', 'target_level', 'phone', 'parent_name', 'parent_phone', 'school']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'level': forms.Select(attrs={'class': 'form-select'}),
            'target_level': forms.Select(attrs={'class': 'form-select'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'parent_name': forms.TextInput(attrs={'class': 'form-control'}),
            'parent_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'school': forms.TextInput(attrs={'class': 'form-control'}),
        }

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

class PracticeRecordForm(forms.ModelForm):
    """练琴记录表单"""
    class Meta:
        model = PracticeRecord
        fields = ['date', 'start_time', 'end_time', 'duration', 'piano_number']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'duration': forms.NumberInput(attrs={'class': 'form-control'}),
            'piano_number': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 7}),
        }

class AttendanceForm(forms.ModelForm):
    """考勤记录表单"""
    class Meta:
        model = Attendance
        fields = ['date', 'check_in_time', 'check_out_time', 'status']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'check_in_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'check_out_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

class SheetMusicSearchForm(forms.Form):
    """曲谱搜索表单"""
    search_query = forms.CharField(
        label='搜索曲谱',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '输入曲谱名称或作曲家...'})
    )
    
    DIFFICULTY_CHOICES = [
        ('', '所有难度'),
        ('beginner', '初级'),
        ('intermediate', '中级'),
        ('advanced', '高级'),
    ]
    
    GENRE_CHOICES = [
        ('', '所有曲风'),
        ('classical', '古典'),
        ('pop', '流行'),
        ('jazz', '爵士'),
        ('folk', '民谣'),
    ]
    
    difficulty = forms.ChoiceField(
        label='难度等级',
        choices=DIFFICULTY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    genre = forms.ChoiceField(
        label='曲风分类',
        choices=GENRE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
