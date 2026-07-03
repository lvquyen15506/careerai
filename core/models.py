"""
Models cho Nền tảng AI Kết nối Việc làm Sinh viên.
Bao gồm: StudentProfile, EmployerProfile, JobShift, ShiftApplication, TimeBlock.
"""
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class StudentProfile(models.Model):
    """
    Hồ sơ sinh viên - quan hệ 1-1 với User.
    Chứa thông tin cá nhân và điểm uy tín.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_profile',
        verbose_name='Tài khoản'
    )
    student_code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Mã sinh viên',
        help_text='Tự động trích xuất từ email'
    )
    full_name = models.CharField(max_length=150, verbose_name='Họ và tên')
    class_name = models.CharField(max_length=50, verbose_name='Lớp sinh hoạt')
    major = models.CharField(max_length=100, verbose_name='Ngành học')
    avatar = models.FileField(
        upload_to='student_avatars/',
        blank=True,
        null=True,
        verbose_name='Ảnh đại diện'
    )
    trust_score = models.FloatField(
        default=5.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(10.0)],
        verbose_name='Điểm uy tín'
    )
    is_profile_complete = models.BooleanField(
        default=False,
        verbose_name='Đã hoàn thiện hồ sơ'
    )
    portal_school = models.CharField(
        max_length=50,
        blank=True,
        default='',
        verbose_name='Trường portal'
    )
    portal_password = models.CharField(
        max_length=128,
        blank=True,
        default='',
        verbose_name='Mật khẩu portal'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ngày tạo')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Cập nhật lần cuối')

    class Meta:
        db_table = 'student_profile'
        verbose_name = 'Hồ sơ Sinh viên'
        verbose_name_plural = 'Hồ sơ Sinh viên'

    def __str__(self):
        return f"{self.full_name} ({self.student_code})"


class EmployerProfile(models.Model):
    """
    Hồ sơ doanh nghiệp - quan hệ 1-1 với User.
    Cần được admin kiểm duyệt (is_verified).
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='employer_profile',
        verbose_name='Tài khoản'
    )
    company_name = models.CharField(max_length=200, verbose_name='Tên công ty')
    address = models.TextField(verbose_name='Địa chỉ')
    business_license = models.CharField(
        max_length=50,
        verbose_name='Mã giấy phép kinh doanh'
    )
    is_verified = models.BooleanField(
        default=False,
        verbose_name='Đã xác minh',
        help_text='Admin kiểm duyệt doanh nghiệp'
    )
    trust_score = models.FloatField(
        default=5.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(10.0)],
        verbose_name='Điểm uy tín'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ngày tạo')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Cập nhật lần cuối')

    class Meta:
        db_table = 'employer_profile'
        verbose_name = 'Hồ sơ Doanh nghiệp'
        verbose_name_plural = 'Hồ sơ Doanh nghiệp'

    def __str__(self):
        return self.company_name


class JobShift(models.Model):
    """
    Ca làm việc - do doanh nghiệp tạo.
    Trạng thái: Open (đang mở), Filled (đã đủ người), Closed (đã đóng).
    """
    STATUS_CHOICES = [
        ('Open', 'Đang mở'),
        ('Filled', 'Đã đủ người'),
        ('Closed', 'Đã đóng'),
    ]

    SCHOOL_CHOICES = [
        ('Tất cả', 'Tất cả các trường'),
        ('ictu', 'ĐH CNTT & Truyền thông (ICTU)'),
        ('tueba', 'ĐH Kinh tế & QTKD (TUEBA)'),
        ('tnut', 'ĐH Kỹ thuật Công nghiệp (TNUT)'),
        ('tnus', 'ĐH Khoa học (TNUS)'),
        ('tump', 'ĐH Y Dược (TUMP)'),
        ('tnue', 'ĐH Sư phạm (TNUE)'),
        ('sfl', 'Trường Ngoại ngữ (SFL)'),
    ]

    MAJOR_CHOICES = [
        ('Tất cả', 'Tất cả các ngành'),
        ('Công nghệ thông tin', 'Công nghệ thông tin'),
        ('Kỹ thuật phần mềm', 'Kỹ thuật phần mềm'),
        ('Khoa học máy tính', 'Khoa học máy tính'),
        ('Hệ thống thông tin quản lý', 'Hệ thống thông tin quản lý'),
        ('Quản trị kinh doanh', 'Quản trị kinh doanh'),
        ('Kế toán', 'Kế toán'),
        ('Tài chính ngân hàng', 'Tài chính ngân hàng'),
        ('Kỹ thuật cơ khí', 'Kỹ thuật cơ khí'),
        ('Kỹ thuật điện', 'Kỹ thuật điện'),
        ('Tự động hóa', 'Tự động hóa'),
        ('Y đa khoa', 'Y đa khoa'),
        ('Dược học', 'Dược học'),
        ('Ngôn ngữ Anh', 'Ngôn ngữ Anh'),
        ('Ngôn ngữ Trung Quốc', 'Ngôn ngữ Trung Quốc'),
        ('Sư phạm toán', 'Sư phạm toán'),
        ('Sư phạm văn', 'Sư phạm văn'),
        ('Khác', 'Khác'),
    ]

    employer = models.ForeignKey(
        EmployerProfile,
        on_delete=models.CASCADE,
        related_name='job_shifts',
        verbose_name='Doanh nghiệp'
    )
    title = models.CharField(max_length=200, verbose_name='Tiêu đề ca làm')
    description = models.TextField(
        blank=True,
        default='',
        verbose_name='Mô tả công việc'
    )
    start_time = models.DateTimeField(verbose_name='Thời gian bắt đầu')
    end_time = models.DateTimeField(verbose_name='Thời gian kết thúc')
    registration_deadline = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Hạn đăng ký ca làm'
    )
    wage_per_hour = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        verbose_name='Lương/giờ (VNĐ)',
        help_text='Đơn vị: VNĐ'
    )
    required_students = models.PositiveIntegerField(
        default=1,
        verbose_name='Số sinh viên cần'
    )
    target_school = models.CharField(
        max_length=50,
        choices=SCHOOL_CHOICES,
        default='Tất cả',
        verbose_name='Trường yêu cầu'
    )
    target_major = models.CharField(
        max_length=100,
        choices=MAJOR_CHOICES,
        default='Tất cả',
        verbose_name='Ngành yêu cầu'
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='Open',
        verbose_name='Trạng thái'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ngày tạo')

    class Meta:
        db_table = 'job_shift'
        verbose_name = 'Ca làm việc'
        verbose_name_plural = 'Ca làm việc'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.employer.company_name}"

    @property
    def accepted_count(self):
        """Số sinh viên đã nhận ca này."""
        return self.applications.exclude(status='Pending').count()

    @property
    def is_available(self):
        """Kiểm tra ca còn chỗ trống không."""
        return self.status == 'Open' and self.accepted_count < self.required_students


class ShiftApplication(models.Model):
    """
    Đơn ứng tuyển ca làm - liên kết sinh viên với ca.
    Luồng: Pending -> CheckIn -> CheckOut -> Completed
    """
    STATUS_CHOICES = [
        ('Pending', 'Chờ duyệt'),
        ('CheckIn', 'Đã check-in'),
        ('CheckOut', 'Đã check-out'),
        ('Completed', 'Hoàn thành'),
        ('Failed', 'Không hoàn thành'),
    ]

    shift = models.ForeignKey(
        JobShift,
        on_delete=models.CASCADE,
        related_name='applications',
        verbose_name='Ca làm'
    )
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='applications',
        verbose_name='Sinh viên'
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='Pending',
        verbose_name='Trạng thái'
    )
    check_in_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Thời gian check-in'
    )
    check_out_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Thời gian check-out'
    )
    rating_from_employer = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Đánh giá từ doanh nghiệp'
    )
    rating_from_student = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Đánh giá từ sinh viên'
    )
    applied_at = models.DateTimeField(auto_now_add=True, verbose_name='Ngày ứng tuyển')

    class Meta:
        db_table = 'shift_application'
        verbose_name = 'Đơn ứng tuyển'
        verbose_name_plural = 'Đơn ứng tuyển'
        unique_together = ['shift', 'student']

    def __str__(self):
        return f"{self.student} - {self.shift.title}"


class TimeBlock(models.Model):
    """
    Khung thời gian rảnh của sinh viên.
    Dùng cho thuật toán Smart Matching để gợi ý ca phù hợp.
    """
    WEEKDAY_CHOICES = [
        (0, 'Thứ Hai'),
        (1, 'Thứ Ba'),
        (2, 'Thứ Tư'),
        (3, 'Thứ Năm'),
        (4, 'Thứ Sáu'),
        (5, 'Thứ Bảy'),
        (6, 'Chủ Nhật'),
    ]

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='time_blocks',
        verbose_name='Sinh viên'
    )
    weekday = models.IntegerField(
        choices=WEEKDAY_CHOICES,
        verbose_name='Ngày trong tuần'
    )
    start_time = models.TimeField(verbose_name='Giờ bắt đầu rảnh')
    end_time = models.TimeField(verbose_name='Giờ kết thúc rảnh')

    class Meta:
        db_table = 'time_block'
        verbose_name = 'Khung giờ rảnh'
        verbose_name_plural = 'Khung giờ rảnh'
        ordering = ['weekday', 'start_time']

    def __str__(self):
        return f"{self.get_weekday_display()}: {self.start_time} - {self.end_time}"


class StudySchedule(models.Model):
    """
    Thời khóa biểu học tập của sinh viên - cào từ ĐKTC.
    Dùng để dựng Timeline hiển thị.
    """
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='study_schedules',
        verbose_name='Sinh viên'
    )
    course_code = models.CharField(max_length=50, verbose_name='Mã học phần', blank=True, default='')
    course_name = models.CharField(max_length=200, verbose_name='Tên học phần')
    credits = models.CharField(max_length=10, verbose_name='Số tín chỉ', blank=True, default='')
    lop = models.CharField(max_length=100, verbose_name='Lớp học phần', blank=True, default='')
    weekday = models.IntegerField(choices=TimeBlock.WEEKDAY_CHOICES, verbose_name='Ngày trong tuần') # 0-6
    tiet = models.CharField(max_length=50, verbose_name='Tiết học') # e.g. "1-3" or "7-9"
    phong = models.CharField(max_length=50, verbose_name='Phòng học', blank=True, default='')
    start_date = models.DateField(null=True, blank=True, verbose_name='Ngày bắt đầu')
    end_date = models.DateField(null=True, blank=True, verbose_name='Ngày kết thúc')
    giang_vien = models.CharField(max_length=150, blank=True, default='', verbose_name='Giảng viên')
    link_meet = models.URLField(max_length=500, blank=True, default='', verbose_name='Link Google Meet')

    class Meta:
        db_table = 'study_schedule'
        verbose_name = 'Lịch học sinh viên'
        verbose_name_plural = 'Lịch học sinh viên'

    def __str__(self):
        return f"{self.course_name} ({self.tiet}): {self.phong}"


class ExamSchedule(models.Model):
    """
    Lịch thi học phần của sinh viên - cào từ ĐKTC.
    """
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='exam_schedules',
        verbose_name='Sinh viên'
    )
    course_code = models.CharField(max_length=50, verbose_name='Mã học phần', blank=True, default='')
    course_name = models.CharField(max_length=200, verbose_name='Tên học phần')
    exam_date = models.DateField(verbose_name='Ngày thi')
    exam_time = models.TimeField(verbose_name='Giờ thi')
    room = models.CharField(max_length=50, verbose_name='Phòng thi', blank=True, default='')
    exam_format = models.CharField(max_length=100, verbose_name='Hình thức thi', blank=True, default='Trắc nghiệm')
    sbd = models.CharField(max_length=20, verbose_name='Số báo danh', blank=True, default='')
    notes = models.TextField(blank=True, default='', verbose_name='Ghi chú')

    class Meta:
        db_table = 'exam_schedule'
        verbose_name = 'Lịch thi sinh viên'
        verbose_name_plural = 'Lịch thi sinh viên'
        ordering = ['exam_date', 'exam_time']

    def __str__(self):
        return f"Thi {self.course_name} - {self.exam_date} {self.exam_time}"
