from django import forms
from .models import Payment, PaymentCategory, Fee, FinancialStatement

class PaymentForm(forms.ModelForm):
    """付款记录表单"""
    class Meta:
        model = Payment
        fields = ['student', 'category', 'amount', 'status', 'payment_date', 'notes']
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': '请输入备注信息'}),
        }
        labels = {
            'student': '学生 *',
            'category': '付款类别 *',
            'amount': '金额 *',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 添加Bootstrap样式
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            if field_name == 'status':
                field.widget.attrs['class'] += ' form-select'
                # 简化状态选项
                field.choices = [
                    ('pending', '待支付'),
                    ('paid', '已支付')
                ]
        
        # 确保类别包含所有PaymentCategory
        self.fields['category'].queryset = PaymentCategory.objects.all()

class PaymentCategoryForm(forms.ModelForm):
    """付款类别表单"""
    class Meta:
        model = PaymentCategory
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 添加Bootstrap样式
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

class FeeForm(forms.ModelForm):
    """费用标准表单"""
    class Meta:
        model = Fee
        fields = ['name', 'category', 'amount', 'description', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 添加Bootstrap样式
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            if field_name == 'category':
                field.widget.attrs['class'] += ' form-select'
            if field_name == 'is_active':
                field.widget.attrs['class'] = 'form-check-input'
