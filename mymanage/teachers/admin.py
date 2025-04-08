from django.contrib import admin
from .models import TeacherProfile, PrivacySetting
from django.contrib import messages

@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    """教师管理"""
    list_display = ('name', 'user', 'phone', 'gender', 'created_at')
    search_fields = ('name', 'user__username', 'phone')
    list_filter = ('gender', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['reset_password']
    fieldsets = (
        ('基本信息', {
            'fields': ('user', 'name', 'gender', 'phone', 'avatar', 'bio')
        }),
        ('教学信息', {
            'fields': ('specialties',)
        }),
        ('系统信息', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def reset_password(self, request, queryset):
        """重置所选教师的密码"""
        for teacher in queryset:
            if not teacher.user:
                continue
                
            # 生成随机密码
            from django.utils.crypto import get_random_string
            new_password = get_random_string(8)
            
            # 设置新密码
            teacher.user.set_password(new_password)
            teacher.user.save()
            
            # 显示消息
            self.message_user(
                request, 
                f"已重置教师 {teacher.name} 的密码为: {new_password}",
                messages.SUCCESS
            )
    
    reset_password.short_description = "重置所选教师的密码"

@admin.register(PrivacySetting)
class PrivacySettingAdmin(admin.ModelAdmin):
    """教师隐私设置管理"""
    list_display = ('teacher', 'phone_visibility', 'email_visibility', 'bio_visibility')
    list_filter = ('phone_visibility', 'email_visibility', 'bio_visibility')
    search_fields = ('teacher__name', 'teacher__user__username')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(teacher__user=request.user)
    
    def has_add_permission(self, request):
        if hasattr(request.user, 'teacher_profile'):
            # 检查用户是否已有隐私设置
            return not PrivacySetting.objects.filter(teacher=request.user.teacher_profile).exists()
        return False
