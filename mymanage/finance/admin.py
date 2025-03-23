from django.contrib import admin
from .models import (
    PaymentCategory, Payment, Tuition, 
    TuitionPayment, Expense
)


@admin.register(PaymentCategory)
class PaymentCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category_type', 'description']
    list_filter = ['category_type']
    search_fields = ['name', 'description']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'amount', 'category', 'payment_type', 
        'payment_date', 'student', 'course', 'teacher'
    ]
    list_filter = ['payment_type', 'payment_date', 'category']
    search_fields = ['description', 'receipt_number']
    date_hierarchy = 'payment_date'
    raw_id_fields = ['student', 'course', 'teacher']


@admin.register(Tuition)
class TuitionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'student', 'course', 'amount', 'paid_amount',
        'status', 'due_date', 'created_at'
    ]
    list_filter = ['status', 'due_date', 'created_at']
    search_fields = ['student__name', 'course__name']
    date_hierarchy = 'created_at'
    raw_id_fields = ['student', 'course', 'enrollment']
    readonly_fields = ['paid_amount', 'status']


@admin.register(TuitionPayment)
class TuitionPaymentAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'tuition', 'amount', 'payment_type',
        'payment_date', 'receipt_number'
    ]
    list_filter = ['payment_type', 'payment_date']
    search_fields = ['receipt_number', 'tuition__student__name']
    date_hierarchy = 'payment_date'
    raw_id_fields = ['tuition', 'recorded_by']


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'amount', 'expense_type', 'payment_type',
        'expense_date', 'teacher', 'invoice_number'
    ]
    list_filter = ['expense_type', 'payment_type', 'expense_date']
    search_fields = ['description', 'invoice_number', 'teacher__name']
    date_hierarchy = 'expense_date'
    raw_id_fields = ['teacher', 'recorded_by']
