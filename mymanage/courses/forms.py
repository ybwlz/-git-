from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Course, CourseSchedule, Enrollment, Piano, SheetMusic


class CourseForm(forms.ModelForm):
    """
    课程创建/编辑表单
    """
    class Meta:
        model = Course
        fields = ['name', 'code', 'level', 'description', 'teacher', 
                 'max_students', 'start_date', 'end_date', 'tuition_fee']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            # 确保开始日期不晚于结束日期
            if start_date > end_date:
                raise ValidationError('开始日期不能晚于结束日期')
            
            # 确保开始日期不早于今天
            today = timezone.now().date()
            if start_date < today:
                raise ValidationError('开始日期不能早于今天')
        
        return cleaned_data


class CourseScheduleForm(forms.ModelForm):
    """
    课程安排表单
    """
    class Meta:
        model = CourseSchedule
        fields = ['course', 'weekday', 'start_time', 'end_time']
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        weekday = cleaned_data.get('weekday')
        course = cleaned_data.get('course')
        
        if start_time and end_time:
            # 确保开始时间早于结束时间
            if start_time >= end_time:
                raise ValidationError('开始时间必须早于结束时间')
            
            # 检查与现有课程安排的冲突
            if self.instance.pk:
                # 排除当前编辑的课程安排
                existing_schedules = CourseSchedule.objects.filter(
                    weekday=weekday
                ).exclude(pk=self.instance.pk)
            else:
                existing_schedules = CourseSchedule.objects.filter(weekday=weekday)
            
            for schedule in existing_schedules:
                if (start_time < schedule.end_time and end_time > schedule.start_time):
                    raise ValidationError(f'此时间段与课程"{schedule.course.name}"的安排冲突')
        
        return cleaned_data


class EnrollmentForm(forms.ModelForm):
    """
    学生报名表单
    """
    class Meta:
        model = Enrollment
        fields = ['course', 'student', 'payment_status']
    
    def __init__(self, *args, **kwargs):
        # 可以传入可选参数student，限制只能为特定学生报名
        student = kwargs.pop('student', None)
        super().__init__(*args, **kwargs)
        
        if student:
            self.fields['student'].initial = student
            self.fields['student'].widget = forms.HiddenInput()
        
        # 只显示未满的活跃课程
        active_courses = Course.objects.filter(status='active')
        available_courses = [course for course in active_courses if not course.is_full()]
        self.fields['course'].queryset = Course.objects.filter(pk__in=[c.pk for c in available_courses])
    
    def clean(self):
        cleaned_data = super().clean()
        course = cleaned_data.get('course')
        student = cleaned_data.get('student')
        
        if course and student:
            # 检查课程是否已满
            if course.is_full() and not self.instance.pk:
                raise ValidationError(f'课程"{course.name}"已满')
            
            # 检查学生是否已经报名此课程
            if Enrollment.objects.filter(student=student, course=course).exists() and not self.instance.pk:
                raise ValidationError('该学生已经报名了此课程')
        
        return cleaned_data


class PianoForm(forms.ModelForm):
    """
    钢琴信息表单
    """
    class Meta:
        model = Piano
        fields = ['piano_number', 'location']


class SheetMusicForm(forms.ModelForm):
    """
    曲谱上传表单
    """
    class Meta:
        model = SheetMusic
        fields = ['title', 'composer', 'level', 'description', 'sheet_file']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        # 可以传入当前教师
        teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)
        self.teacher = teacher
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.teacher:
            instance.uploaded_by = self.teacher
        
        if commit:
            instance.save()
        return instance


class SheetMusicSearchForm(forms.Form):
    """
    曲谱搜索表单
    """
    title = forms.CharField(label='曲谱标题', required=False)
    composer = forms.CharField(label='作曲家', required=False)
    level = forms.ChoiceField(
        label='难度等级', 
        choices=[('', '------')] + list(SheetMusic.LEVEL_CHOICES),
        required=False
    )
