from django.contrib import admin
from .models import Student, PracticeRecord, Attendance, SheetMusic, SheetMusicPage, StudentFavorite

class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'level', 'phone', 'school', 'created_at')
    search_fields = ('name', 'phone', 'parent_name', 'parent_phone')
    list_filter = ('level', 'created_at')

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

class AttendanceAdmin(admin.ModelAdmin):
    """旧版考勤记录的管理配置，保留兼容性"""
    list_display = ('student', 'date', 'check_in_time', 'check_out_time', 'status')
    search_fields = ('student__name',)
    list_filter = ('date', 'status')
    date_hierarchy = 'date'
    
    def has_add_permission(self, request):
        """禁用添加旧版考勤记录"""
        return False

class SheetMusicAdmin(admin.ModelAdmin):
    list_display = ('title', 'composer', 'difficulty', 'genre', 'upload_time', 'is_active')
    search_fields = ('title', 'composer', 'description')
    list_filter = ('difficulty', 'genre', 'is_active')

class SheetMusicPageAdmin(admin.ModelAdmin):
    list_display = ('sheet_music', 'page_number')
    search_fields = ('sheet_music__title',)
    list_filter = ('sheet_music',)

class StudentFavoriteAdmin(admin.ModelAdmin):
    list_display = ('student', 'sheet_music', 'created_at')
    search_fields = ('student__name', 'sheet_music__title')
    list_filter = ('created_at',)

# 注册模型到管理后台
admin.site.register(Student, StudentAdmin)
admin.site.register(PracticeRecord, PracticeRecordAdmin)
admin.site.register(Attendance, AttendanceAdmin)
admin.site.register(SheetMusic, SheetMusicAdmin)
admin.site.register(SheetMusicPage, SheetMusicPageAdmin)
admin.site.register(StudentFavorite, StudentFavoriteAdmin)
