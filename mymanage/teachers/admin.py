from django.contrib import admin
from .models import TeacherProfile, TeacherCertificate, NotificationSetting, PrivacySetting

@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    """教师个人信息管理"""
    list_display = ('name', 'user', 'phone', 'gender', 'created_at')
    search_fields = ('name', 'user__username', 'phone')
    list_filter = ('gender', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
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

@admin.register(TeacherCertificate)
class TeacherCertificateAdmin(admin.ModelAdmin):
    """教师证书管理"""
    list_display = ('title', 'teacher', 'issue_date', 'expire_date', 'is_verified')
    list_filter = ('is_verified', 'issue_date')
    search_fields = ('title', 'teacher__name', 'certificate_no')
    readonly_fields = ('created_at',)
    fieldsets = (
        ('证书信息', {
            'fields': ('teacher', 'title', 'certificate_no', 'issuing_authority', 'image')
        }),
        ('日期信息', {
            'fields': ('issue_date', 'expire_date')
        }),
        ('验证信息', {
            'fields': ('is_verified', 'created_at')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(teacher__user=request.user)

@admin.register(NotificationSetting)
class NotificationSettingAdmin(admin.ModelAdmin):
    """教师通知设置管理"""
    list_display = ('teacher', 'course_reminder', 'attendance_reminder', 'fee_reminder', 'in_app', 'sms', 'email')
    list_filter = ('course_reminder', 'attendance_reminder', 'fee_reminder', 'in_app', 'sms', 'email')
    search_fields = ('teacher__name', 'teacher__user__username')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(teacher__user=request.user)
    
    def has_add_permission(self, request):
        if hasattr(request.user, 'teacher_profile'):
            # 检查用户是否已有通知设置
            return not NotificationSetting.objects.filter(teacher=request.user.teacher_profile).exists()
        return False

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
