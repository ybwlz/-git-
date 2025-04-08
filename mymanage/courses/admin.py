from django.contrib import admin
from .models import PianoLevel, Piano, Course, CourseSchedule, SheetMusic


@admin.register(PianoLevel)
class PianoLevelAdmin(admin.ModelAdmin):
    list_display = ('level', 'description')
    search_fields = ('level', 'description')


@admin.register(Piano)
class PianoAdmin(admin.ModelAdmin):
    list_display = ('number', 'brand', 'model', 'is_active', 'is_occupied')
    list_filter = ('is_active', 'is_occupied', 'brand')
    search_fields = ('number', 'brand', 'model', 'notes')
    ordering = ('number',)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'level', 'teacher', 'duration')
    list_filter = ('level', 'teacher')
    search_fields = ('name', 'code', 'description')
    ordering = ('level', 'name')


@admin.register(CourseSchedule)
class CourseScheduleAdmin(admin.ModelAdmin):
    list_display = ('course', 'get_weekday_display', 'start_time', 'end_time', 'is_active')
    list_filter = ('weekday', 'is_active', 'course')
    search_fields = ('course__name',)
    ordering = ('weekday', 'start_time')


@admin.register(SheetMusic)
class SheetMusicAdmin(admin.ModelAdmin):
    list_display = ('title', 'composer', 'level', 'upload_date', 'is_public')
    list_filter = ('level', 'is_public', 'upload_date')
    search_fields = ('title', 'composer', 'description')
    # 注释掉date_hierarchy以解决时区问题
    # date_hierarchy = 'upload_date'
    readonly_fields = ('uploaded_by', 'upload_date')
