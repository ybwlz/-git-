from django.contrib import admin
from .models import QRCode, AttendanceSession, AttendanceRecord, WaitingQueue


@admin.register(QRCode)
class QRCodeAdmin(admin.ModelAdmin):
    list_display = ('id', 'course', 'created_at', 'expires_at', 'is_valid')
    list_filter = ('course', 'created_at')
    search_fields = ('course__name', 'course__code')
    readonly_fields = ('uuid',)


@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'course', 'start_time', 'end_time', 'status', 'created_by')
    list_filter = ('course', 'status', 'start_time')
    search_fields = ('course__name',)
    readonly_fields = ('start_time',)


class PianoInline(admin.TabularInline):
    model = AttendanceRecord
    extra = 0
    fields = ('student', 'piano', 'status', 'check_in_time', 'check_out_time', 'duration')
    readonly_fields = ('check_in_time', 'check_out_time', 'duration')


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'student', 'piano', 'status', 'check_in_time', 'check_out_time', 'duration')
    list_filter = ('session__course', 'status', 'check_in_time')
    search_fields = ('student__name', 'student__student_id', 'session__course__name')
    readonly_fields = ('check_in_time', 'duration')


@admin.register(WaitingQueue)
class WaitingQueueAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'student', 'join_time', 'estimated_wait_time', 'is_active')
    list_filter = ('session__course', 'is_active', 'join_time')
    search_fields = ('student__name', 'student__student_id', 'session__course__name')
    readonly_fields = ('join_time',)
