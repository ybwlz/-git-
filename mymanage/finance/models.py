from django.db import models
from django.utils import timezone
from mymanage.students.models import Student
from mymanage.teachers.models import Teacher
from mymanage.courses.models import Course, Enrollment


class PaymentCategory(models.Model):
    """
    支付类别模型
    """
    CATEGORY_TYPE_CHOICES = (
        ('income', '收入'),
        ('expense', '支出'),
    )
    
    name = models.CharField('类别名称', max_length=50)
    category_type = models.CharField('类别类型', max_length=10, choices=CATEGORY_TYPE_CHOICES)
    description = models.TextField('说明', blank=True)
    
    class Meta:
        verbose_name = '支付类别'
        verbose_name_plural = '支付类别'
        
    def __str__(self):
        return f"{self.name} ({self.get_category_type_display()})"


class Payment(models.Model):
    """
    支付记录模型
    """
    PAYMENT_TYPE_CHOICES = (
        ('cash', '现金'),
        ('wechat', '微信'),
        ('alipay', '支付宝'),
        ('bank_transfer', '银行转账'),
        ('other', '其他'),
    )
    
    amount = models.DecimalField('金额', max_digits=10, decimal_places=2)
    category = models.ForeignKey(PaymentCategory, on_delete=models.PROTECT, related_name='payments', verbose_name='类别')
    payment_type = models.CharField('支付方式', max_length=20, choices=PAYMENT_TYPE_CHOICES, default='cash')
    payment_date = models.DateField('支付日期', default=timezone.now)
    description = models.TextField('备注', blank=True)
    receipt_number = models.CharField('收据号', max_length=50, blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    # 收入关联的学生或课程，支出关联的教师
    student = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments', verbose_name='学生')
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments', verbose_name='课程')
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True, related_name='expense_payments', verbose_name='教师')
    
    class Meta:
        verbose_name = '支付记录'
        verbose_name_plural = '支付记录'
        ordering = ['-payment_date', '-created_at']
        
    def __str__(self):
        return f"{self.category.name} - ¥{self.amount} - {self.payment_date}"
    
    @property
    def is_income(self):
        """是否为收入"""
        return self.category.category_type == 'income'


class Tuition(models.Model):
    """
    学费记录模型，专门用于记录学生缴纳的学费
    """
    STATUS_CHOICES = (
        ('pending', '待缴费'),
        ('partial', '部分缴费'),
        ('paid', '已缴费'),
        ('overdue', '逾期'),
        ('refunded', '已退款'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='tuitions', verbose_name='学生')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='tuitions', verbose_name='课程')
    enrollment = models.OneToOneField(Enrollment, on_delete=models.CASCADE, related_name='tuition', verbose_name='报名记录')
    amount = models.DecimalField('应缴金额', max_digits=10, decimal_places=2)
    paid_amount = models.DecimalField('已缴金额', max_digits=10, decimal_places=2, default=0)
    status = models.CharField('状态', max_length=10, choices=STATUS_CHOICES, default='pending')
    due_date = models.DateField('截止日期')
    payment_date = models.DateField('缴费日期', null=True, blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        verbose_name = '学费记录'
        verbose_name_plural = '学费记录'
        ordering = ['-due_date']
        
    def __str__(self):
        return f"{self.student.name} - {self.course.name} - ¥{self.amount}"
    
    @property
    def remaining_amount(self):
        """剩余应缴金额"""
        return self.amount - self.paid_amount
    
    @property
    def is_fully_paid(self):
        """是否已全额缴费"""
        return self.paid_amount >= self.amount
    
    def update_status(self):
        """更新缴费状态"""
        if self.status == 'refunded':
            return
            
        if self.paid_amount >= self.amount:
            self.status = 'paid'
            if not self.payment_date:
                self.payment_date = timezone.now().date()
        elif self.paid_amount > 0:
            self.status = 'partial'
        elif timezone.now().date() > self.due_date:
            self.status = 'overdue'
        else:
            self.status = 'pending'
        self.save()


class TuitionPayment(models.Model):
    """
    学费支付记录，记录每次学费缴纳的详情
    """
    tuition = models.ForeignKey(Tuition, on_delete=models.CASCADE, related_name='payments', verbose_name='学费记录')
    amount = models.DecimalField('缴费金额', max_digits=10, decimal_places=2)
    payment_type = models.CharField('支付方式', max_length=20, choices=Payment.PAYMENT_TYPE_CHOICES, default='cash')
    payment_date = models.DateField('缴费日期', default=timezone.now)
    receipt_number = models.CharField('收据号', max_length=50, blank=True)
    recorded_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, related_name='recorded_tuition_payments', verbose_name='记录人')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    
    class Meta:
        verbose_name = '学费支付记录'
        verbose_name_plural = '学费支付记录'
        ordering = ['-payment_date', '-created_at']
        
    def __str__(self):
        return f"{self.tuition.student.name} - ¥{self.amount} - {self.payment_date}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # 更新学费记录的已缴金额
        tuition = self.tuition
        tuition.paid_amount = tuition.payments.aggregate(models.Sum('amount'))['amount__sum'] or 0
        tuition.update_status()
        
        # 同时创建一个对应的支付记录
        # 获取或创建一个"学费收入"类别
        income_category, _ = PaymentCategory.objects.get_or_create(
            name='学费收入',
            category_type='income',
            defaults={'description': '学生缴纳的学费'}
        )
        
        # 创建支付记录
        Payment.objects.create(
            amount=self.amount,
            category=income_category,
            payment_type=self.payment_type,
            payment_date=self.payment_date,
            description=f"{self.tuition.student.name}缴纳{self.tuition.course.name}课程学费",
            receipt_number=self.receipt_number,
            student=self.tuition.student,
            course=self.tuition.course
        )


class Expense(models.Model):
    """
    支出记录模型，用于记录琴行的各项支出
    """
    EXPENSE_TYPE_CHOICES = (
        ('rent', '房租'),
        ('utility', '水电费'),
        ('salary', '工资'),
        ('maintenance', '维修费'),
        ('purchase', '采购费'),
        ('tax', '税费'),
        ('insurance', '保险费'),
        ('marketing', '营销费'),
        ('other', '其他'),
    )
    
    amount = models.DecimalField('金额', max_digits=10, decimal_places=2)
    expense_type = models.CharField('支出类型', max_length=20, choices=EXPENSE_TYPE_CHOICES)
    payment_type = models.CharField('支付方式', max_length=20, choices=Payment.PAYMENT_TYPE_CHOICES, default='cash')
    expense_date = models.DateField('支出日期', default=timezone.now)
    description = models.TextField('备注', blank=True)
    invoice_number = models.CharField('发票号', max_length=50, blank=True)
    recorded_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, related_name='recorded_expenses', verbose_name='记录人')
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True, related_name='salary_expenses', verbose_name='教师')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    
    class Meta:
        verbose_name = '支出记录'
        verbose_name_plural = '支出记录'
        ordering = ['-expense_date', '-created_at']
        
    def __str__(self):
        return f"{self.get_expense_type_display()} - ¥{self.amount} - {self.expense_date}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # 同时创建一个对应的支付记录
        # 获取或创建一个对应支出类别
        expense_category, _ = PaymentCategory.objects.get_or_create(
            name=self.get_expense_type_display(),
            category_type='expense',
            defaults={'description': f'{self.get_expense_type_display()}类支出'}
        )
        
        # 创建支付记录
        Payment.objects.create(
            amount=self.amount,
            category=expense_category,
            payment_type=self.payment_type,
            payment_date=self.expense_date,
            description=self.description,
            receipt_number=self.invoice_number,
            teacher=self.teacher
        )
