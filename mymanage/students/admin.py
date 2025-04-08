from django.contrib import admin
from .models import Student, PracticeRecord
from django.contrib.auth.forms import PasswordResetForm
from django.contrib import messages

class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'level', 'phone', 'school', 'created_at')
    search_fields = ('name', 'phone', 'parent_name', 'parent_phone')
    list_filter = ('level', 'created_at')
    actions = ['reset_password']
    
    def reset_password(self, request, queryset):
        """重置所选学生的密码"""
        for student in queryset:
            if not student.user:
                continue
                
            # 生成随机密码
            from django.utils.crypto import get_random_string
            new_password = get_random_string(8)
            
            # 设置新密码
            student.user.set_password(new_password)
            student.user.save()
            
            # 显示消息
            self.message_user(
                request, 
                f"已重置学生 {student.name} 的密码为: {new_password}",
                messages.SUCCESS
            )
    
    reset_password.short_description = "重置所选学生的密码"

class PracticeRecordAdmin(admin.ModelAdmin):
    """练琴记录（主要考勤记录）的管理配置"""
    list_display = ('student', 'date', 'start_time', 'end_time', 'duration', 'piano_number', 'status')
    search_fields = ('student__name',)
    list_filter = ('date', 'status', 'piano_number')
    date_hierarchy = 'date'
    
    def get_queryset(self, request):
        """默认显示最近7天的记录"""
        qs = super().get_queryset(request)
        from django.utils import timezone
        from datetime import timedelta
        seven_days_ago = timezone.now().date() - timedelta(days=7)
        return qs.filter(date__gte=seven_days_ago)

# 注册模型到管理后台
admin.site.register(Student, StudentAdmin)
admin.site.register(PracticeRecord, PracticeRecordAdmin)
