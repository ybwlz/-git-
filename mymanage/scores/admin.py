from django.contrib import admin
from django.db.models import Avg, Count, Case, When, Sum
from .models import ExamType, Exam, Score, ScoreDetail, ScoreStatistics, PerformanceLevel


class ExamTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')


class ExamAdmin(admin.ModelAdmin):
    list_display = ('name', 'exam_type', 'course', 'teacher', 'exam_date', 'status', 
                    'student_count', 'average_score', 'pass_rate')
    list_filter = ('status', 'exam_type', 'exam_date', 'course', 'teacher')
    search_fields = ('name', 'description', 'location')
    date_hierarchy = 'exam_date'
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'exam_type', 'description', 'course', 'teacher')
        }),
        ('考试信息', {
            'fields': ('exam_date', 'start_time', 'end_time', 'status', 'max_score', 'passing_score', 'location')
        }),
        ('其他信息', {
            'fields': ('notes', 'created_at', 'updated_at')
        }),
    )
    
    def student_count(self, obj):
        return obj.student_count
    student_count.short_description = '学生数'
    
    def average_score(self, obj):
        return obj.average_score
    average_score.short_description = '平均分'
    
    def pass_rate(self, obj):
        return f'{obj.pass_rate:.1f}%' if obj.pass_rate is not None else '0.0%'
    pass_rate.short_description = '及格率'


class ScoreDetailInline(admin.TabularInline):
    model = ScoreDetail
    extra = 1


class ScoreAdmin(admin.ModelAdmin):
    list_display = ('student', 'exam', 'score', 'is_passing', 'is_absent', 'created_by', 'created_at')
    list_filter = ('exam__exam_type', 'is_absent', 'created_at')
    search_fields = ('student__name', 'exam__name', 'comment')
    raw_id_fields = ('student', 'exam')
    inlines = [ScoreDetailInline]
    readonly_fields = ('created_at', 'updated_at', 'created_by')
    
    def is_passing(self, obj):
        return obj.is_passing
    is_passing.boolean = True
    is_passing.short_description = '是否及格'


class ScoreDetailAdmin(admin.ModelAdmin):
    list_display = ('score', 'item_name', 'point', 'max_point', 'weight', 'comment')
    list_filter = ('score__exam',)
    search_fields = ('item_name', 'comment')
    raw_id_fields = ('score',)


class ScoreStatisticsAdmin(admin.ModelAdmin):
    list_display = ('course', 'exam_count', 'student_count', 'average_score', 
                   'highest_score', 'lowest_score', 'pass_rate', 'statistics_date')
    list_filter = ('statistics_date', 'course')
    search_fields = ('course__name',)
    date_hierarchy = 'statistics_date'
    readonly_fields = ('created_at',)
    
    def pass_rate(self, obj):
        return f'{obj.pass_rate:.1f}%'
    pass_rate.short_description = '及格率'


class PerformanceLevelAdmin(admin.ModelAdmin):
    list_display = ('name', 'min_score', 'max_score', 'color_code', 'is_active', 'description')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')


# 注册模型
admin.site.register(ExamType, ExamTypeAdmin)
admin.site.register(Exam, ExamAdmin)
admin.site.register(Score, ScoreAdmin)
admin.site.register(ScoreDetail, ScoreDetailAdmin)
admin.site.register(ScoreStatistics, ScoreStatisticsAdmin)
admin.site.register(PerformanceLevel, PerformanceLevelAdmin)
