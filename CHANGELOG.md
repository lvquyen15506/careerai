# CHANGELOG - Nền tảng AI Kết nối Việc làm Sinh viên ICTU

## [1.0.0] - 2026-06-30

### ✅ Giai đoạn 1: Cấu hình Khởi tạo
- Tạo virtual environment (`venv`) với Python 3.12.0
- Cài đặt dependencies qua pip:
  - Django 4.2.17
  - mysqlclient 2.2.7
  - django-allauth 65.4.1
  - django-crispy-forms 2.3
  - crispy-bootstrap5 2024.10
  - python-dotenv 1.1.0
  - requests 2.34.2
  - PyJWT 2.13.0
  - cryptography 49.0.0
- Tạo Django project `student_job_platform` với các file:
  - `manage.py` - Entry point
  - `student_job_platform/settings.py` - Cấu hình MySQL, allauth, Bootstrap 5, tiếng Việt
  - `student_job_platform/urls.py` - URL routing chính (admin, allauth, core)
  - `student_job_platform/wsgi.py` - WSGI config
  - `student_job_platform/asgi.py` - ASGI config
- Tạo file `.env` cho biến môi trường (DB, OAuth keys)
- Tạo `requirements.txt` đầy đủ

### ✅ Giai đoạn 2: Database Models
- Tạo app `core` với các models:
  - `StudentProfile` (1-1 User): student_code, full_name, class_name, major, trust_score
  - `EmployerProfile` (1-1 User): company_name, address, business_license, is_verified, trust_score
  - `JobShift` (FK Employer): title, start/end_time, wage_per_hour, required_students, status (Open/Filled/Closed)
  - `ShiftApplication` (FK Shift + Student): status (Pending/CheckIn/CheckOut/Completed), check_in/out_time, ratings
  - `TimeBlock` (FK Student): weekday, start_time, end_time (lịch rảnh cho Smart Matching)
- Tạo `admin.py` với:
  - Custom admin cho tất cả models
  - Actions tùy chỉnh: Duyệt/Từ chối doanh nghiệp
  - Bộ lọc, tìm kiếm, hiển thị chi tiết

### ✅ Giai đoạn 3: Core Logic (Services & Authentication)
- `services.py`:
  - `extract_student_code(email)`: Trích mã SV từ email @ictu.edu.vn
  - `smart_match(student)`: Thuật toán gợi ý ca khớp 100% thời gian rảnh
  - `update_trust_score(profile, rating)`: Cập nhật điểm uy tín trung bình (thang 10)
- `adapters.py`:
  - `ICTUAccountAdapter`: Chặn email không phải @ictu.edu.vn
  - `ICTUSocialAccountAdapter`: Kiểm tra email khi SSO, tự tạo StudentProfile
- `forms.py`:
  - StudentProfileForm, EmployerProfileForm, JobShiftForm, TimeBlockForm, RatingForm
  - Tất cả có Bootstrap 5 classes tích hợp sẵn

### ✅ Giai đoạn 4: Views & URLs
- `views.py` (15 views):
  - `home_view`: Chuyển hướng theo vai trò
  - `complete_profile_view`: Bổ sung thông tin SV + khung giờ rảnh
  - `student_dashboard_view`: Dashboard SV (gợi ý, ca đang nhận, lịch sử)
  - `employer_dashboard_view`: Dashboard DN (quản lý ca, duyệt chấm công)
  - `create_shift_view`: Tạo ca làm mới
  - `shift_detail_view`: Chi tiết ca (khác cho SV và DN)
  - `apply_shift_view`: Sinh viên nhận ca
  - `check_in_view` / `check_out_view`: Chấm công
  - `rate_view`: Đánh giá sao (1-5) + cập nhật trust_score
  - `add_time_block_view` / `delete_time_block_view`: Quản lý lịch rảnh
  - `register_employer_view`: Đăng ký doanh nghiệp
- `core/urls.py`: 14 URL patterns

### ✅ Giai đoạn 5: Frontend Templates (Bootstrap 5)
- `base.html`: Layout chung - Dark gradient navbar, custom CSS design system (glassmorphism, gradients, animations)
- `dashboard_student.html`: 4 stat cards, bảng ca gợi ý, ca đang nhận, lịch sử
- `dashboard_employer.html`: Thống kê, bảng chấm công cần duyệt, danh sách ca
- `complete_profile.html`: Form 2 cột (thông tin + lịch rảnh)
- `create_shift.html`: Form tạo ca với datetime-local input
- `shift_detail.html`: Chi tiết ca + sidebar hành động (Check-in/out)
- `rate.html`: Đánh giá sao tương tác (hover + click JS)
- `register_employer.html`: Form đăng ký DN
- `account/login.html`: Trang đăng nhập SSO (Google + Microsoft buttons)
- `account/logout.html`: Xác nhận đăng xuất

### 🔧 Verification
- `python manage.py check` → **System check identified no issues (0 silenced)** ✅

---

## Cấu trúc thư mục hoàn chỉnh

```
d:\STKN\SRC\
├── manage.py
├── requirements.txt
├── .env
├── readme.md
├── CHANGELOG.md
├── student_job_platform/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── core/
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py          (5 models)
│   ├── admin.py            (5 admin classes)
│   ├── services.py         (3 functions)
│   ├── adapters.py         (2 adapters)
│   ├── forms.py            (5 forms)
│   ├── views.py            (15 views)
│   ├── urls.py             (14 patterns)
│   ├── migrations/
│   └── templates/
│       ├── core/
│       │   ├── base.html
│       │   ├── dashboard_student.html
│       │   ├── dashboard_employer.html
│       │   ├── complete_profile.html
│       │   ├── create_shift.html
│       │   ├── shift_detail.html
│       │   ├── rate.html
│       │   └── register_employer.html
│       └── account/
│           ├── login.html
│           └── logout.html
├── static/
│   └── css/
└── venv/
```

---

## Bước tiếp theo để chạy

1. Tạo database MySQL: `CREATE DATABASE student_job_db CHARACTER SET utf8mb4;`
2. Cập nhật `.env` với thông tin MySQL thật
3. Chạy migrations: `python manage.py makemigrations && python manage.py migrate`
4. Tạo superuser: `python manage.py createsuperuser`
5. Chạy server: `python manage.py runserver`
6. Cấu hình OAuth keys (Google Cloud Console / Azure AD) nếu muốn dùng SSO
