"""
Django Admin configuration cho dự án Việc làm Sinh viên.
Cho phép quản trị viên kiểm duyệt doanh nghiệp và quản lý dữ liệu.
"""
from django.contrib import admin
from .models import (
    StudentProfile,
    EmployerProfile,
    JobShift,
    ShiftApplication,
    TimeBlock,
    StudySchedule,
    ExamSchedule,
)


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    """Admin cho hồ sơ sinh viên."""
    list_display = ('student_code', 'full_name', 'class_name', 'major', 'trust_score', 'is_profile_complete')
    list_filter = ('major', 'class_name', 'is_profile_complete')
    search_fields = ('student_code', 'full_name', 'user__email')
    readonly_fields = ('student_code', 'created_at', 'updated_at')


@admin.register(EmployerProfile)
class EmployerProfileAdmin(admin.ModelAdmin):
    """
    Admin cho hồ sơ doanh nghiệp.
    Action tùy chỉnh: duyệt/từ chối doanh nghiệp.
    """
    list_display = ('company_name', 'business_license', 'is_verified', 'trust_score', 'created_at')
    list_filter = ('is_verified',)
    search_fields = ('company_name', 'business_license', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['approve_employers', 'reject_employers']

    @admin.action(description='✅ Duyệt doanh nghiệp đã chọn')
    def approve_employers(self, request, queryset):
        """Duyệt xác minh các doanh nghiệp đã chọn."""
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'Đã duyệt {updated} doanh nghiệp.')

    @admin.action(description='❌ Từ chối doanh nghiệp đã chọn')
    def reject_employers(self, request, queryset):
        """Từ chối xác minh các doanh nghiệp đã chọn."""
        updated = queryset.update(is_verified=False)
        self.message_user(request, f'Đã từ chối {updated} doanh nghiệp.')


@admin.register(JobShift)
class JobShiftAdmin(admin.ModelAdmin):
    """Admin cho ca làm việc."""
    list_display = ('title', 'employer', 'start_time', 'end_time', 'wage_per_hour', 'required_students', 'status')
    list_filter = ('status', 'employer')
    search_fields = ('title', 'employer__company_name')
    date_hierarchy = 'start_time'


@admin.register(ShiftApplication)
class ShiftApplicationAdmin(admin.ModelAdmin):
    """Admin cho đơn ứng tuyển ca làm."""
    list_display = (
        'student', 'shift', 'status',
        'check_in_time', 'check_out_time',
        'rating_from_employer', 'rating_from_student',
        'applied_at'
    )
    list_filter = ('status',)
    search_fields = ('student__full_name', 'shift__title')
    readonly_fields = ('applied_at',)


@admin.register(TimeBlock)
class TimeBlockAdmin(admin.ModelAdmin):
    """Admin cho khung giờ rảnh sinh viên."""
    list_display = ('student', 'weekday', 'start_time', 'end_time')
    list_filter = ('weekday',)
    search_fields = ('student__full_name',)


@admin.register(StudySchedule)
class StudyScheduleAdmin(admin.ModelAdmin):
    """Admin cho lịch học sinh viên."""
    list_display = ('student', 'course_name', 'lop', 'weekday', 'tiet', 'phong', 'giang_vien')
    list_filter = ('weekday', 'phong')
    search_fields = ('student__full_name', 'course_name', 'giang_vien')


@admin.register(ExamSchedule)
class ExamScheduleAdmin(admin.ModelAdmin):
    """Admin cho lịch thi sinh viên."""
    list_display = ('student', 'course_name', 'exam_date', 'exam_time', 'room', 'exam_format', 'sbd')
    list_filter = ('exam_date', 'room', 'exam_format')
    search_fields = ('student__full_name', 'course_name', 'room')
