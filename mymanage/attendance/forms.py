from django import forms
from django.utils import timezone
import datetime

from .models import AttendanceSession, AttendanceRecord
from mymanage.courses.models import Course, CourseSchedule


class SessionCreateForm(forms.ModelForm):
    """考勤会话创建表单"""
    class Meta:
        model = AttendanceSession
        fields = ['course', 'schedule']
        widgets = {
            'course': forms.Select(attrs={'class': 'form-control'}),
            'schedule': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # 如果提供了用户，则仅显示该用户为教师的课程
        if user:
            self.fields['course'].queryset = Course.objects.filter(teacher__user=user)
            self.fields['schedule'].queryset = CourseSchedule.objects.filter(course__teacher__user=user)


class AttendanceRecordForm(forms.ModelForm):
    """考勤记录表单（用于教师手动添加/编辑考勤记录）"""
    class Meta:
        model = AttendanceRecord
        fields = ['student', 'piano', 'check_in_time', 'check_out_time', 'status', 'notes']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'piano': forms.Select(attrs={'class': 'form-control'}),
            'check_in_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'check_out_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        session = kwargs.pop('session', None)
        super().__init__(*args, **kwargs)
        
        # 如果提供会话，则自动设置并且设为只读
        if session:
            self.fields['session'] = forms.ModelChoiceField(
                queryset=AttendanceSession.objects.filter(id=session.id),
                initial=session,
                widget=forms.HiddenInput()
            )
    
    def clean(self):
        cleaned_data = super().clean()
        check_in_time = cleaned_data.get('check_in_time')
        check_out_time = cleaned_data.get('check_out_time')
        
        # 确保签退时间在签到时间之后
        if check_in_time and check_out_time and check_out_time <= check_in_time:
            self.add_error('check_out_time', '签退时间必须在签到时间之后')
        
        return cleaned_data


class DateRangeFilterForm(forms.Form):
    """日期范围过滤表单"""
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 默认显示当前月的日期范围
        today = timezone.now().date()
        first_day = today.replace(day=1)
        if not self.is_bound:
            self.fields['start_date'].initial = first_day
            self.fields['end_date'].initial = today
