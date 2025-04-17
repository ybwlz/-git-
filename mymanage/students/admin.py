from django.contrib import admin
from .models import Student, PracticeRecord, Attendance
from django.contrib.auth.forms import PasswordResetForm
from django.contrib import messages
from django.utils import timezone

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

@admin.register(PracticeRecord)
class PracticeRecordAdmin(admin.ModelAdmin):
    """练琴记录（主要考勤记录）的管理配置"""
    list_display = ('student', 'date', 'start_time', 'get_end_time_display', 'get_duration_display', 'piano_number', 'status')
    list_filter = ('status', 'date', 'student')
    search_fields = ('student__name', 'piano_number')
    ordering = ('-date', '-start_time')
    
    def get_end_time_display(self, obj):
        if obj.status == 'active':
            return '练琴中'
        return obj.end_time
    get_end_time_display.short_description = '结束时间'
    
    def get_duration_display(self, obj):
        if obj.status == 'active':
            # 如果是进行中的记录，计算当前时长
            current_time = timezone.now()
            duration_minutes = int((current_time - obj.start_time).total_seconds() / 60)
            return f'{duration_minutes}分钟（进行中）'
        if obj.duration is not None:
            return f'{obj.duration}分钟'
        if obj.end_time and obj.start_time:
            # 如果有开始和结束时间但没有duration，计算时长
            duration_minutes = int((obj.end_time - obj.start_time).total_seconds() / 60)
            return f'{duration_minutes}分钟'
        return '-'
    get_duration_display.short_description = '练习时长'

# 注册模型到管理后台
admin.site.register(Student, StudentAdmin)
