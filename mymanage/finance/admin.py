from django.contrib import admin
from .models import PaymentCategory, Payment


@admin.register(PaymentCategory)
class PaymentCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('student', 'category', 'amount', 'payment_method', 'status', 'payment_date', 'created_by')
    list_filter = ('status', 'payment_method', 'category', 'payment_date')
    search_fields = ('student__name', 'notes')
    # 注释掉date_hierarchy以解决时区问题
    # date_hierarchy = 'created_at'
