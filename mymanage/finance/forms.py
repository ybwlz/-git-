from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, date, timedelta
from decimal import Decimal

from .models import Payment, PaymentCategory, Tuition, TuitionPayment, Expense
from mymanage.courses.models import Course, Enrollment


class PaymentCategoryForm(forms.ModelForm):
    """
    支付类别表单
    """
    class Meta:
        model = PaymentCategory
        fields = ['name', 'category_type', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3})
        }


class PaymentForm(forms.ModelForm):
    """
    支付记录表单
    """
    class Meta:
        model = Payment
        fields = ['amount', 'category', 'payment_type', 'payment_date', 
                  'description', 'receipt_number', 'student', 'course', 'teacher']
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 初始值为今天日期
        if not self.initial.get('payment_date'):
            self.initial['payment_date'] = timezone.now().date()
        
        # 分别设置收入和支出类别
        income_categories = PaymentCategory.objects.filter(category_type='income')
        expense_categories = PaymentCategory.objects.filter(category_type='expense')
        
        # 动态添加类别选择的帮助文本
        self.fields['category'].help_text = """选择支付类别，收入类别包括：
        {}；支出类别包括：{}""".format(
            ', '.join([c.name for c in income_categories]),
            ', '.join([c.name for c in expense_categories])
        )
    
    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        student = cleaned_data.get('student')
        course = cleaned_data.get('course')
        teacher = cleaned_data.get('teacher')
        
        if category:
            # 收入类别必须关联学生或课程
            if category.category_type == 'income':
                if not (student or course):
                    raise ValidationError('收入记录必须关联学生或课程')
                if teacher:
                    raise ValidationError('收入记录不应关联教师')
                    
            # 支出类别可以关联教师
            if category.category_type == 'expense':
                if student or course:
                    raise ValidationError('支出记录不应关联学生或课程')
        
        return cleaned_data


class TuitionForm(forms.ModelForm):
    """
    学费记录表单
    """
    class Meta:
        model = Tuition
        fields = ['student', 'course', 'amount', 'due_date']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 设置合理的默认截止日期（一个月后）
        if not self.initial.get('due_date'):
            self.initial['due_date'] = timezone.now().date() + timedelta(days=30)
        
        # 如果是新创建的学费记录，过滤只显示尚未创建学费记录的报名记录
        if not self.instance.pk:
            # 获取已有学费记录的报名ID
            existing_tuition_enrollments = Tuition.objects.values_list('enrollment_id', flat=True)
            # 过滤课程选项，只显示有效且尚未缴费的课程
            valid_enrollments = Enrollment.objects.filter(
                status='active'
            ).exclude(
                id__in=existing_tuition_enrollments
            )
            
            valid_courses = Course.objects.filter(
                enrollments__in=valid_enrollments
            ).distinct()
            
            self.fields['course'].queryset = valid_courses
            
            # 根据选择的课程自动填充金额
            self.fields['course'].widget.attrs.update({
                'onchange': 'updateTuitionAmount(this.value)'
            })
    
    def clean(self):
        cleaned_data = super().clean()
        student = cleaned_data.get('student')
        course = cleaned_data.get('course')
        
        if student and course:
            # 验证学生是否已报名此课程
            try:
                enrollment = Enrollment.objects.get(student=student, course=course)
                cleaned_data['enrollment'] = enrollment
            except Enrollment.DoesNotExist:
                raise ValidationError('该学生未报名此课程')
                
            # 验证学生是否已创建过此课程的学费记录
            if not self.instance.pk and Tuition.objects.filter(student=student, course=course).exists():
                raise ValidationError('该学生已创建过此课程的学费记录')
        
        # 验证截止日期不早于今天
        due_date = cleaned_data.get('due_date')
        if due_date and due_date < timezone.now().date():
            raise ValidationError('截止日期不能早于今天')
        
        return cleaned_data


class TuitionPaymentForm(forms.ModelForm):
    """
    学费支付记录表单
    """
    class Meta:
        model = TuitionPayment
        fields = ['tuition', 'amount', 'payment_type', 'payment_date', 'receipt_number']
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date'})
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        tuition_id = kwargs.pop('tuition_id', None)
        super().__init__(*args, **kwargs)
        
        # 保存当前用户作为记录人
        self.user = user
        
        # 初始值为今天日期
        if not self.initial.get('payment_date'):
            self.initial['payment_date'] = timezone.now().date()
        
        # 如果传入了tuition_id参数，固定学费记录
        if tuition_id:
            self.fields['tuition'].queryset = Tuition.objects.filter(id=tuition_id)
            self.fields['tuition'].initial = tuition_id
            self.fields['tuition'].widget = forms.HiddenInput()
            
            # 获取学费记录信息
            try:
                tuition = Tuition.objects.get(id=tuition_id)
                remaining = tuition.remaining_amount
                # 默认金额为剩余金额
                self.fields['amount'].initial = remaining
                # 添加剩余金额提示
                self.fields['amount'].help_text = f'剩余应缴金额: ¥{remaining}'
            except Tuition.DoesNotExist:
                pass
        else:
            # 只显示未全额缴费的学费记录
            unpaid_tuitions = Tuition.objects.exclude(status='paid')
            self.fields['tuition'].queryset = unpaid_tuitions
    
    def clean(self):
        cleaned_data = super().clean()
        tuition = cleaned_data.get('tuition')
        amount = cleaned_data.get('amount')
        
        if tuition and amount:
            # 验证缴费金额不超过剩余应缴金额
            if amount > tuition.remaining_amount:
                raise ValidationError(f'缴费金额(¥{amount})超过剩余应缴金额(¥{tuition.remaining_amount})')
            
            # 验证缴费金额为正数
            if amount <= 0:
                raise ValidationError('缴费金额必须为正数')
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.recorded_by = self.user
        
        if commit:
            instance.save()
        return instance


class ExpenseForm(forms.ModelForm):
    """
    支出记录表单
    """
    class Meta:
        model = Expense
        fields = ['amount', 'expense_type', 'payment_type', 'expense_date', 
                  'description', 'invoice_number', 'teacher']
        widgets = {
            'expense_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3})
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # 保存当前用户作为记录人
        self.user = user
        
        # 初始值为今天日期
        if not self.initial.get('expense_date'):
            self.initial['expense_date'] = timezone.now().date()
    
    def clean(self):
        cleaned_data = super().clean()
        amount = cleaned_data.get('amount')
        expense_type = cleaned_data.get('expense_type')
        teacher = cleaned_data.get('teacher')
        
        # 如果是工资支出，必须指定教师
        if expense_type == 'salary' and not teacher:
            raise ValidationError('工资支出必须指定教师')
        
        # 验证支出金额为正数
        if amount and amount <= 0:
            raise ValidationError('支出金额必须为正数')
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.recorded_by = self.user
        
        if commit:
            instance.save()
        return instance


class FinancialReportForm(forms.Form):
    """
    财务报表查询表单
    """
    report_type = forms.ChoiceField(
        label='报表类型', 
        choices=[
            ('income', '收入报表'),
            ('expense', '支出报表'),
            ('tuition', '学费报表'),
            ('profit', '收支利润报表'),
        ]
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
    period = forms.ChoiceField(
        label='时间周期',
        choices=[
            ('', '自定义日期范围'),
            ('current_month', '本月'),
            ('last_month', '上月'),
            ('current_year', '今年'),
            ('last_year', '去年'),
            ('last_30_days', '最近30天'),
            ('last_90_days', '最近90天'),
        ],
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 如果没有默认值，设置默认为本月
        if not self.initial.get('period'):
            self.initial['period'] = 'current_month'
        if not self.initial.get('report_type'):
            self.initial['report_type'] = 'income'
    
    def clean(self):
        cleaned_data = super().clean()
        period = cleaned_data.get('period')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        today = timezone.now().date()
        
        # 如果选择了预定义周期，设置相应的日期范围
        if period == 'current_month':
            start_date = date(today.year, today.month, 1)
            # 下个月第一天减一天，得到当月最后一天
            next_month = today.replace(day=28) + timedelta(days=4)
            end_date = next_month.replace(day=1) - timedelta(days=1)
            
        elif period == 'last_month':
            # 上个月第一天
            first_day_of_month = today.replace(day=1)
            last_month = first_day_of_month - timedelta(days=1)
            start_date = date(last_month.year, last_month.month, 1)
            end_date = first_day_of_month - timedelta(days=1)
            
        elif period == 'current_year':
            start_date = date(today.year, 1, 1)
            end_date = date(today.year, 12, 31)
            
        elif period == 'last_year':
            start_date = date(today.year - 1, 1, 1)
            end_date = date(today.year - 1, 12, 31)
            
        elif period == 'last_30_days':
            start_date = today - timedelta(days=30)
            end_date = today
            
        elif period == 'last_90_days':
            start_date = today - timedelta(days=90)
            end_date = today
        
        # 如果没有选择预定义周期，但提供了自定义日期范围
        if not period and (start_date or end_date):
            # 如果只提供了开始日期，默认结束日期为今天
            if start_date and not end_date:
                end_date = today
            # 如果只提供了结束日期，默认开始日期为结束日期前30天
            elif end_date and not start_date:
                start_date = end_date - timedelta(days=30)
        
        # 如果都没有提供，默认为本月
        if not start_date and not end_date:
            start_date = date(today.year, today.month, 1)
            next_month = today.replace(day=28) + timedelta(days=4)
            end_date = next_month.replace(day=1) - timedelta(days=1)
        
        # 确保开始日期不晚于结束日期
        if start_date and end_date and start_date > end_date:
            raise ValidationError('开始日期不能晚于结束日期')
        
        # 更新日期值
        cleaned_data['start_date'] = start_date
        cleaned_data['end_date'] = end_date
        
        return cleaned_data
