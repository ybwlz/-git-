from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.forms import inlineformset_factory
from datetime import datetime

from .models import ExamType, Exam, Score, ScoreDetail, PerformanceLevel
from mymanage.students.models import Student
from mymanage.courses.models import Course, Enrollment


class ExamTypeForm(forms.ModelForm):
    """
    考试类型表单
    """
    class Meta:
        model = ExamType
        fields = ['name', 'description', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class ExamForm(forms.ModelForm):
    """
    考试表单
    """
    class Meta:
        model = Exam
        fields = [
            'name', 'exam_type', 'description', 'course', 'teacher',
            'exam_date', 'start_time', 'end_time', 'status',
            'max_score', 'passing_score', 'location', 'notes'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'exam_date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 设置默认值
        if not self.initial.get('exam_date'):
            self.initial['exam_date'] = timezone.now().date()
        if not self.initial.get('start_time'):
            self.initial['start_time'] = '09:00'
        if not self.initial.get('end_time'):
            self.initial['end_time'] = '11:00'
    
    def clean(self):
        cleaned_data = super().clean()
        exam_date = cleaned_data.get('exam_date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        # 验证考试日期不早于今天
        if exam_date and exam_date < timezone.now().date():
            self.add_error('exam_date', '考试日期不能早于今天')
        
        # 验证开始时间不晚于结束时间
        if start_time and end_time and start_time >= end_time:
            self.add_error('start_time', '开始时间必须早于结束时间')
        
        return cleaned_data


class ScoreForm(forms.ModelForm):
    """
    成绩表单
    """
    class Meta:
        model = Score
        fields = ['student', 'exam', 'score', 'comment', 'is_absent']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        exam_id = kwargs.pop('exam_id', None)
        super().__init__(*args, **kwargs)
        
        if exam_id:
            # 如果提供了考试ID，只显示该考试
            self.fields['exam'].queryset = Exam.objects.filter(id=exam_id)
            self.fields['exam'].initial = exam_id
            self.fields['exam'].widget = forms.HiddenInput()
            
            # 获取考试信息
            try:
                exam = Exam.objects.get(id=exam_id)
                # 只显示参加该课程的学生
                enrolled_students = Student.objects.filter(
                    enrollments__course=exam.course,
                    enrollments__status='active'
                ).distinct()
                
                # 排除已有成绩的学生
                if not self.instance.pk:  # 只在创建新记录时过滤
                    existing_student_ids = Score.objects.filter(exam=exam).values_list('student_id', flat=True)
                    enrolled_students = enrolled_students.exclude(id__in=existing_student_ids)
                
                self.fields['student'].queryset = enrolled_students
                
                # 设置分数上限
                self.fields['score'].widget.attrs['max'] = exam.max_score
                self.fields['score'].validators[1] = forms.validators.MaxValueValidator(exam.max_score)
            except Exam.DoesNotExist:
                pass
    
    def clean(self):
        cleaned_data = super().clean()
        is_absent = cleaned_data.get('is_absent')
        score = cleaned_data.get('score')
        
        # 如果学生缺席，分数应为0
        if is_absent and score and score > 0:
            cleaned_data['score'] = 0
            self.add_error('score', '学生缺席时分数应为0')
        
        return cleaned_data


class ScoreDetailForm(forms.ModelForm):
    """
    成绩详情表单
    """
    class Meta:
        model = ScoreDetail
        fields = ['item_name', 'max_point', 'point', 'weight', 'comment']
    
    def clean(self):
        cleaned_data = super().clean()
        max_point = cleaned_data.get('max_point')
        point = cleaned_data.get('point')
        
        # 验证得分不超过满分
        if point and max_point and point > max_point:
            self.add_error('point', '得分不能超过满分')
        
        return cleaned_data


# 创建内联表单集，用于一次性提交多个成绩详情
ScoreDetailFormSet = inlineformset_factory(
    Score, ScoreDetail,
    form=ScoreDetailForm,
    extra=3,  # 默认显示3个空表单
    can_delete=True  # 允许删除
)


class BatchScoreForm(forms.Form):
    """
    批量录入成绩表单
    """
    exam = forms.ModelChoiceField(
        label='考试',
        queryset=Exam.objects.filter(status__in=['pending', 'ongoing']),
        empty_label=None
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 动态添加学生成绩字段
        exam_id = self.data.get('exam') if self.data else self.initial.get('exam')
        
        if exam_id:
            try:
                exam = Exam.objects.get(id=exam_id)
                # 获取尚未录入成绩的学生
                enrolled_students = Student.objects.filter(
                    enrollments__course=exam.course,
                    enrollments__status='active'
                ).distinct()
                
                existing_student_ids = Score.objects.filter(exam=exam).values_list('student_id', flat=True)
                students_to_grade = enrolled_students.exclude(id__in=existing_student_ids)
                
                for student in students_to_grade:
                    self.fields[f'score_{student.id}'] = forms.DecimalField(
                        label=f'{student.name} 分数',
                        max_digits=5,
                        decimal_places=1,
                        required=False,
                        min_value=0,
                        max_value=exam.max_score
                    )
                    self.fields[f'absent_{student.id}'] = forms.BooleanField(
                        label=f'{student.name} 缺席',
                        required=False
                    )
                    self.fields[f'comment_{student.id}'] = forms.CharField(
                        label=f'{student.name} 评语',
                        widget=forms.Textarea(attrs={'rows': 2}),
                        required=False
                    )
            except Exam.DoesNotExist:
                pass


class PerformanceLevelForm(forms.ModelForm):
    """
    表现等级表单
    """
    class Meta:
        model = PerformanceLevel
        fields = ['name', 'min_score', 'max_score', 'description', 'color_code', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'color_code': forms.TextInput(attrs={'type': 'color'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        min_score = cleaned_data.get('min_score')
        max_score = cleaned_data.get('max_score')
        
        # 验证最低分不高于最高分
        if min_score and max_score and min_score > max_score:
            self.add_error('min_score', '最低分不能高于最高分')
        
        return cleaned_data


class ScoreSearchForm(forms.Form):
    """
    成绩查询表单
    """
    student = forms.ModelChoiceField(
        label='学生',
        queryset=Student.objects.all(),
        required=False
    )
    course = forms.ModelChoiceField(
        label='课程',
        queryset=Course.objects.all(),
        required=False
    )
    exam_type = forms.ModelChoiceField(
        label='考试类型',
        queryset=ExamType.objects.filter(is_active=True),
        required=False
    )
    start_date = forms.DateField(
        label='开始日期',
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False
    )
    end_date = forms.DateField(
        label='结束日期',
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False
    )
    min_score = forms.DecimalField(
        label='最低分数',
        max_digits=5,
        decimal_places=1,
        required=False,
        min_value=0,
        max_value=100
    )
    max_score = forms.DecimalField(
        label='最高分数',
        max_digits=5,
        decimal_places=1,
        required=False,
        min_value=0,
        max_value=100
    )
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        min_score = cleaned_data.get('min_score')
        max_score = cleaned_data.get('max_score')
        
        # 验证开始日期不晚于结束日期
        if start_date and end_date and start_date > end_date:
            self.add_error('start_date', '开始日期不能晚于结束日期')
        
        # 验证最低分不高于最高分
        if min_score and max_score and min_score > max_score:
            self.add_error('min_score', '最低分不能高于最高分')
        
        return cleaned_data


class ScoreStatisticsForm(forms.Form):
    """
    成绩统计表单
    """
    course = forms.ModelChoiceField(
        label='课程',
        queryset=Course.objects.all(),
        required=True
    )
    exam_type = forms.ModelChoiceField(
        label='考试类型',
        queryset=ExamType.objects.filter(is_active=True),
        required=False
    )
    start_date = forms.DateField(
        label='开始日期',
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False
    )
    end_date = forms.DateField(
        label='结束日期',
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 设置默认值
        if not self.initial.get('start_date'):
            # 默认为当前月份的第一天
            today = timezone.now().date()
            self.initial['start_date'] = today.replace(day=1)
        if not self.initial.get('end_date'):
            # 默认为今天
            self.initial['end_date'] = timezone.now().date()
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        # 验证开始日期不晚于结束日期
        if start_date and end_date and start_date > end_date:
            self.add_error('start_date', '开始日期不能晚于结束日期')
        
        return cleaned_data
