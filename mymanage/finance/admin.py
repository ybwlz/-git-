from django.contrib import admin
from .models import PaymentCategory, Payment, Fee, FinancialStatement


@admin.register(PaymentCategory)
class PaymentCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('student', 'category', 'amount', 'payment_method', 'status', 'payment_date', 'created_by')
    list_filter = ('status', 'payment_method', 'category', 'payment_date')
    search_fields = ('student__name', 'notes')
    date_hierarchy = 'created_at'


@admin.register(Fee)
class FeeAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'amount', 'is_active')
    list_filter = ('is_active', 'category')
    search_fields = ('name', 'description')


@admin.register(FinancialStatement)
class FinancialStatementAdmin(admin.ModelAdmin):
    list_display = ('period', 'start_date', 'end_date', 'total_income', 'generated_by', 'generated_at')
    list_filter = ('period', 'generated_at')
    search_fields = ('notes',)
    date_hierarchy = 'generated_at'
