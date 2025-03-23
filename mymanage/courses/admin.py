from django.contrib import admin
from .models import Course, CourseSchedule, Enrollment, Piano, SheetMusic


class CourseScheduleInline(admin.TabularInline):
    model = CourseSchedule
    extra = 1


class EnrollmentInline(admin.TabularInline):
    model = Enrollment
    extra = 0
    fields = ('student', 'status', 'payment_status', 'enroll_date')
    readonly_fields = ('enroll_date',)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'level', 'teacher', 'status', 'start_date', 'end_date', 'get_current_enrollment_count', 'max_students', 'tuition_fee')
    list_filter = ('status', 'level', 'teacher', 'start_date')
    search_fields = ('name', 'code', 'description', 'teacher__name')
    inlines = [CourseScheduleInline, EnrollmentInline]
    
    def get_current_enrollment_count(self, obj):
        return obj.get_current_enrollment_count()
    get_current_enrollment_count.short_description = '当前报名人数'


@admin.register(CourseSchedule)
class CourseScheduleAdmin(admin.ModelAdmin):
    list_display = ('course', 'get_weekday_display', 'start_time', 'end_time')
    list_filter = ('weekday', 'course__name')
    search_fields = ('course__name',)


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'status', 'payment_status', 'enroll_date')
    list_filter = ('status', 'payment_status', 'course__name', 'enroll_date')
    search_fields = ('student__name', 'student__student_id', 'course__name')
    readonly_fields = ('enroll_date',)


@admin.register(Piano)
class PianoAdmin(admin.ModelAdmin):
    list_display = ('piano_number', 'location', 'is_occupied')
    list_filter = ('is_occupied',)
    search_fields = ('location',)


@admin.register(SheetMusic)
class SheetMusicAdmin(admin.ModelAdmin):
    list_display = ('title', 'composer', 'level', 'uploaded_by', 'upload_date')
    list_filter = ('level', 'composer', 'upload_date')
    search_fields = ('title', 'composer', 'description')
    readonly_fields = ('upload_date',)
