from django.db import models
from django.utils import timezone
from mymanage.students.models import Student
from mymanage.teachers.models import TeacherProfile
from mymanage.users.models import User


class PaymentCategory(models.Model):
    """付款类别"""
    name = models.CharField('类别名称', max_length=50)
    description = models.TextField('描述', blank=True)
    
    class Meta:
        verbose_name = '付款类别'
        verbose_name_plural = '付款类别'
    
    def __str__(self):
        return self.name


class Payment(models.Model):
    """付款记录"""
    PAYMENT_STATUS_CHOICES = (
        ('pending', '待支付'),
        ('paid', '已支付'),
        ('refunded', '已退款'),
        ('cancelled', '已取消'),
    )
    
    PAYMENT_METHOD_CHOICES = (
        ('cash', '现金'),
        ('wechat', '微信'),
        ('alipay', '支付宝'),
        ('bank_transfer', '银行转账'),
        ('other', '其他'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='payments')
    category = models.ForeignKey(PaymentCategory, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField('金额', max_digits=10, decimal_places=2)
    payment_method = models.CharField('支付方式', max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cash')
    status = models.CharField('支付状态', max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_date = models.DateField('支付日期', null=True, blank=True)
    due_date = models.DateField('到期日期', null=True, blank=True)
    notes = models.TextField('备注', blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_payments')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        verbose_name = '付款记录'
        verbose_name_plural = '付款记录'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student.name} - {self.category.name} - {self.amount}"
    
    def save(self, *args, **kwargs):
        # 设置支付日期
        if self.status == 'paid' and not self.payment_date:
            self.payment_date = timezone.now().date()
        super().save(*args, **kwargs)


class Fee(models.Model):
    """费用标准"""
    name = models.CharField('名称', max_length=100)
    category = models.ForeignKey(PaymentCategory, on_delete=models.CASCADE, related_name='fees')
    amount = models.DecimalField('金额', max_digits=10, decimal_places=2)
    description = models.TextField('描述', blank=True)
    is_active = models.BooleanField('是否有效', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    
    class Meta:
        verbose_name = '费用标准'
        verbose_name_plural = '费用标准'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.amount}"


class FinancialStatement(models.Model):
    """财务报表"""
    PERIOD_CHOICES = (
        ('daily', '日报'),
        ('weekly', '周报'),
        ('monthly', '月报'),
        ('yearly', '年报'),
    )
    
    period = models.CharField('周期', max_length=10, choices=PERIOD_CHOICES)
    start_date = models.DateField('开始日期')
    end_date = models.DateField('结束日期')
    total_income = models.DecimalField('总收入', max_digits=10, decimal_places=2)
    notes = models.TextField('备注', blank=True)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='generated_statements')
    generated_at = models.DateTimeField('生成时间', auto_now_add=True)
    
    class Meta:
        verbose_name = '财务报表'
        verbose_name_plural = '财务报表'
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"{self.get_period_display()} - {self.start_date} 至 {self.end_date}"
