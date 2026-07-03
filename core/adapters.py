"""
Custom Allauth Adapter - Chặn email không phải @ictu.edu.vn.
Tự động tạo StudentProfile khi sinh viên đăng nhập lần đầu qua SSO.
"""
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib import messages

from .services import extract_student_code


ALLOWED_DOMAINS = [
    'ictu.edu.vn', 'tueba.edu.vn', 'tnut.edu.vn', 'tnus.edu.vn',
    'sfl.edu.vn', 'tump.edu.vn', 'tnue.edu.vn', 'tnu.edu.vn'
]


def is_allowed_email(email):
    if not email:
        return False
    email_lower = email.lower()
    return any(email_lower.endswith(f"@{domain}") for domain in ALLOWED_DOMAINS)


class ICTUAccountAdapter(DefaultAccountAdapter):
    """
    Adapter tùy chỉnh cho allauth.
    Cho phép đăng nhập bằng email của các trường Đại học Thái Nguyên.
    """

    def is_open_for_signup(self, request):
        return True

    def clean_email(self, email):
        email = super().clean_email(email)
        if not is_allowed_email(email):
            raise ValueError(f"Chỉ chấp nhận email thuộc các trường ĐHTN: {', '.join(ALLOWED_DOMAINS)}")
        return email


class ICTUSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Adapter cho đăng nhập qua Google/Microsoft OAuth.
    Chặn các tài khoản không thuộc miền email ĐHTN.
    """

    def is_open_for_signup(self, request, sociallogin):
        email = sociallogin.account.extra_data.get('email', '')

        if not email:
            user = sociallogin.user
            email = user.email if user else ''

        if not is_allowed_email(email):
            messages.error(
                request,
                f"⚠️ Chỉ chấp nhận tài khoản email thuộc: {', '.join(ALLOWED_DOMAINS)}. "
                "Vui lòng sử dụng email trường của bạn."
            )
            return False
        return True

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)

        from .models import StudentProfile
        student_code = extract_student_code(user.email)

        if student_code and not user.is_staff and not hasattr(user, 'employer_profile') and not hasattr(user, 'student_profile'):
            StudentProfile.objects.create(
                user=user,
                student_code=student_code,
                full_name=user.get_full_name() or student_code,
            )

        return user

