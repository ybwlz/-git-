from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

# 自定义用户管理界面
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'user_type', 'is_active', 'date_joined')
    list_filter = ('user_type', 'is_active')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('个人信息', {'fields': ('user_type', 'phone', 'avatar')}),
        ('权限', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'user_type', 'is_active'),
        }),
    )
    search_fields = ('username', 'phone')
    ordering = ('username',)

# 注册用户模型
admin.site.register(User, CustomUserAdmin)
