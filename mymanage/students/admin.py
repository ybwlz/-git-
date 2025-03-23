from django.contrib import admin
from .models import Student, StudentNotes

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'name', 'gender', 'parent_name', 
                   'parent_phone', 'join_date', 'is_active')
    list_filter = ('gender', 'is_active', 'join_date')
    search_fields = ('name', 'student_id', 'parent_name', 'parent_phone')
    date_hierarchy = 'join_date'
    ordering = ('-join_date',)
    list_editable = ('is_active',)
    list_per_page = 20
    
    fieldsets = (
        ('基本信息', {
            'fields': ('user', 'student_id', 'name', 'gender', 'birth_date')
        }),
        ('联系方式', {
            'fields': ('address', 'parent_name', 'parent_phone')
        }),
        ('状态信息', {
            'fields': ('join_date', 'is_active')
        }),
    )

@admin.register(StudentNotes)
class StudentNotesAdmin(admin.ModelAdmin):
    list_display = ('student', 'title', 'created_at', 'created_by')
    list_filter = ('created_at', 'created_by')
    search_fields = ('student__name', 'student__student_id', 'title', 'content')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    
    fieldsets = (
        ('关联信息', {
            'fields': ('student', 'created_by')
        }),
        ('笔记内容', {
            'fields': ('title', 'content')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # 如果是新建笔记
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
