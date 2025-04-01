from django.contrib import admin
from .models import QRCode, AttendanceSession, AttendanceRecord, WaitingQueue


@admin.register(QRCode)
class QRCodeAdmin(admin.ModelAdmin):
    list_display = ('course', 'created_at', 'expires_at', 'is_valid')
    list_filter = ('course', 'created_at', 'expires_at')
    search_fields = ('course__name',)
    readonly_fields = ('uuid', 'created_at')


@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = ('course', 'start_time', 'end_time', 'status', 'created_by')
    list_filter = ('status', 'course', 'start_time')
    search_fields = ('course__name', 'created_by__username')
    readonly_fields = ('start_time',)


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'session', 'piano', 'check_in_time', 'check_out_time', 'status', 'duration')
    list_filter = ('status', 'check_in_time', 'session')
    search_fields = ('student__name', 'piano__number', 'notes')
    readonly_fields = ('check_in_time', 'duration')


@admin.register(WaitingQueue)
class WaitingQueueAdmin(admin.ModelAdmin):
    list_display = ('student', 'session', 'join_time', 'estimated_wait_time', 'is_active')
    list_filter = ('is_active', 'join_time', 'session')
    search_fields = ('student__name',)
    readonly_fields = ('join_time',)
