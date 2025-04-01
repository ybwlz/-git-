from django.contrib import admin
from .models import Student, PracticeRecord, Attendance, SheetMusic, StudentFavorite

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'level', 'target_level', 'phone', 'school', 'created_at')
    list_filter = ('level', 'target_level', 'school')
    search_fields = ('name', 'phone', 'parent_name', 'parent_phone', 'school')
    ordering = ('-created_at',)

@admin.register(PracticeRecord)
class PracticeRecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'start_time', 'end_time', 'duration', 'piano_number')
    list_filter = ('date', 'piano_number')
    search_fields = ('student__name',)
    ordering = ('-date', '-start_time')

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'check_in_time', 'check_out_time', 'status')
    list_filter = ('date', 'status')
    search_fields = ('student__name',)
    ordering = ('-date', '-check_in_time')

@admin.register(SheetMusic)
class SheetMusicAdmin(admin.ModelAdmin):
    list_display = ('title', 'composer', 'difficulty', 'genre', 'upload_time', 'is_active')
    list_filter = ('difficulty', 'genre', 'is_active')
    search_fields = ('title', 'composer')
    ordering = ('-upload_time',)

@admin.register(StudentFavorite)
class StudentFavoriteAdmin(admin.ModelAdmin):
    list_display = ('student', 'sheet_music', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('student__name', 'sheet_music__title')
    ordering = ('-created_at',)
