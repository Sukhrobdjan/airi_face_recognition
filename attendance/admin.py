from django.contrib import admin
from .models import Employee, AttendanceRecord, Schedule

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'position', 'created_at']
    list_filter = ['position', 'created_at']
    search_fields = ['first_name', 'last_name', 'position']

@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ['employee', 'attendance_type', 'timestamp', 'confidence']
    list_filter = ['attendance_type', 'timestamp']
    search_fields = ['employee__first_name', 'employee__last_name']

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ['employee', 'date', 'start_time', 'end_time']
    list_filter = ['date']
    search_fields = ['employee__first_name', 'employee__last_name']