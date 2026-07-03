"""
Django Forms cho dự án Việc làm Sinh viên.
"""
from django import forms
from .models import StudentProfile, EmployerProfile, JobShift, TimeBlock, ShiftApplication


class StudentProfileForm(forms.ModelForm):
    """Form bổ sung thông tin sinh viên lần đầu đăng nhập."""

    class Meta:
        model = StudentProfile
        fields = ['full_name', 'class_name', 'major', 'avatar']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nguyễn Văn A'
            }),
            'class_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'CNTT-K15A'
            }),
            'major': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Công nghệ thông tin'
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
        }


class AutoSyncProfileForm(forms.Form):
    """Form đồng bộ thông tin tự động từ cổng thông tin đào tạo."""
    
    SCHOOL_CHOICES = [
        ('ictu', 'ĐH CNTT&TT (ICTU)'),
        ('tueba', 'ĐH Kinh tế & QTKD (TUEBA)'),
        ('tump', 'ĐH Y Dược (TUMP)'),
        ('tnue', 'ĐH Sư phạm (TNUE)'),
        ('sfl', 'ĐH Ngoại ngữ (SFL)'),
        ('tnus', 'ĐH Khoa học (TNUS)'),
        ('tnut', 'ĐH Kỹ thuật Công nghiệp (TNUT)'),
    ]

    school = forms.ChoiceField(
        choices=SCHOOL_CHOICES,
        label='Chọn trường đào tạo',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    portal_password = forms.CharField(
        label='Mật khẩu cổng đăng ký tín chỉ (Không bắt buộc)',
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Bỏ trống nếu đã lưu/đồng bộ trước đó'
        }),
        help_text='Mật khẩu này chỉ dùng để lấy thời khóa biểu 1 lần, hệ thống cam kết không lưu trữ lại.'
    )



class EmployerProfileForm(forms.ModelForm):
    """Form đăng ký hồ sơ doanh nghiệp."""

    class Meta:
        model = EmployerProfile
        fields = ['company_name', 'address', 'business_license']
        widgets = {
            'company_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tên công ty/doanh nghiệp'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Địa chỉ doanh nghiệp'
            }),
            'business_license': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Mã giấy phép kinh doanh'
            }),
        }


class JobShiftForm(forms.ModelForm):
    """Form tạo ca làm việc mới."""

    class Meta:
        model = JobShift
        fields = [
            'title', 'description', 'start_time', 'end_time', 'registration_deadline',
            'wage_per_hour', 'required_students', 'target_school', 'target_major'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phục vụ quán cà phê buổi sáng'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Mô tả chi tiết công việc, yêu cầu...'
            }),
            'start_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'end_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'registration_deadline': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'wage_per_hour': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '25000',
                'min': '0'
            }),
            'required_students': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'value': '1'
            }),
            'target_school': forms.Select(attrs={
                'class': 'form-select'
            }),
            'target_major': forms.Select(attrs={
                'class': 'form-select'
            }),
        }


class TimeBlockForm(forms.ModelForm):
    """Form thêm khung giờ rảnh."""

    class Meta:
        model = TimeBlock
        fields = ['weekday', 'start_time', 'end_time']
        widgets = {
            'weekday': forms.Select(attrs={'class': 'form-select'}),
            'start_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'end_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
        }


class RatingForm(forms.Form):
    """Form đánh giá sau ca làm (1-5 sao)."""
    rating = forms.IntegerField(
        min_value=1,
        max_value=5,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'max': '5',
            'placeholder': 'Đánh giá từ 1-5 sao'
        }),
        label='Đánh giá'
    )
