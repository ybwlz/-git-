from django import forms
from django.utils import timezone
from datetime import timedelta
from .models import AttendanceSession, AttendanceRecord, QRCode
from mymanage.courses.models import Course, CourseSchedule


class QRCodeForm(forms.ModelForm):
    """
    二维码生成表单
    """
    expire_minutes = forms.IntegerField(
        label='有效时间(分钟)',
        initial=30,
        min_value=5,
        max_value=120,
        help_text='二维码有效时间，范围5-120分钟'
    )
    
    class Meta:
        model = QRCode
        fields = ['course']
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        # 设置过期时间
        minutes = self.cleaned_data.get('expire_minutes', 30)
        instance.expires_at = timezone.now() + timedelta(minutes=minutes)
        
        if commit:
            instance.save()
        return instance


class AttendanceSessionForm(forms.ModelForm):
    """
    考勤会话创建表单
    """
    class Meta:
        model = AttendanceSession
        fields = ['course', 'schedule']
        
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # 如果是教师用户，只显示该教师的课程
        if user and hasattr(user, 'teacher_profile'):
            self.fields['course'].queryset = Course.objects.filter(teacher=user.teacher_profile)
            
    def save(self, commit=True, user=None):
        instance = super().save(commit=False)
        if user:
            instance.created_by = user
        
        if commit:
            instance.save()
            
            # 自动创建二维码
            qrcode = QRCode.objects.create(
                course=instance.course,
                expires_at=timezone.now() + timedelta(hours=2)
            )
            instance.qrcode = qrcode
            instance.save()
            
        return instance


class StudentCheckInForm(forms.Form):
    """
    学生签到表单
    """
    qrcode_uuid = forms.UUIDField(label='二维码UUID')
    
    def clean_qrcode_uuid(self):
        uuid = self.cleaned_data.get('qrcode_uuid')
        try:
            qrcode = QRCode.objects.get(uuid=uuid)
            if not qrcode.is_valid():
                raise forms.ValidationError('二维码已过期')
            
            # 检查是否有关联的会话
            if not hasattr(qrcode, 'session'):
                raise forms.ValidationError('无效的二维码')
                
            return uuid
        except QRCode.DoesNotExist:
            raise forms.ValidationError('无效的二维码')


class StudentCheckOutForm(forms.Form):
    """
    学生签退表单
    """
    record_id = forms.IntegerField(widget=forms.HiddenInput())
    
    def clean_record_id(self):
        record_id = self.cleaned_data.get('record_id')
        try:
            record = AttendanceRecord.objects.get(id=record_id)
            if record.status != 'checked_in':
                raise forms.ValidationError('该记录已签退')
            return record_id
        except AttendanceRecord.DoesNotExist:
            raise forms.ValidationError('无效的考勤记录')
