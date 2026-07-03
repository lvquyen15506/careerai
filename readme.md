# Student Job Platform (CareerAI)

Ứng dụng web Django giúp kết nối sinh viên với các ca làm ngắn hạn do doanh nghiệp đăng tuyển. Dự án tích hợp đăng nhập SSO (Google / Microsoft), đồng bộ thời khóa biểu từ cổng ĐKTC, thuật toán gợi ý ca phù hợp (Smart Match) và workflow check-in / check-out.

**Nội dung chính**
- `core/` : app chính chứa models, views, forms, services và templates.
- `student_job_platform/settings.py` : cấu hình Django (DB, allauth, dotenv).
- `requirements.txt` : thư viện cần cài.
- `manage.py` : entry point để chạy lệnh Django.

**Yêu cầu**
- Python 3.10+ (hoặc phiên bản tương thích với Django 4.2)
- MySQL (hoặc cấu hình DB tương thích)
- Khuyến nghị: tạo virtual environment (venv)

## Quickstart (chạy local)
1. Tạo và kích hoạt virtualenv
```powershell
python -m venv .venv
.venv\\Scripts\\Activate.ps1
```
2. Cài phụ thuộc
```powershell
pip install -r requirements.txt
```
3. Thiết lập biến môi trường: tạo file `.env` ở gốc repo (xem mẫu bên dưới).
4. Chạy migrate và tạo superuser
```powershell
python manage.py migrate
python manage.py createsuperuser
```
5. Chạy server
```powershell
python manage.py runserver
```

## Biến môi trường (.env) - ví dụ
Tạo file `.env` (KHÔNG commit file này lên git). Ít nhất cần:
```
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=True
DB_NAME=student_job_db
DB_USER=root
DB_PASSWORD=your-db-pass
DB_HOST=127.0.0.1
DB_PORT=3306
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
MICROSOFT_CLIENT_ID=
MICROSOFT_CLIENT_SECRET=
```

## Lưu ý bảo mật
- Không lưu file `.env` hoặc mật khẩu portal (trường `portal_password`) vào kho mã công khai. Hiện model `StudentProfile` có trường `portal_password` — nếu cần đồng bộ tài khoản portal, ưu tiên sử dụng token một lần, mã hoá hoặc yêu cầu người dùng nhập mỗi lần cần đồng bộ.
- Thay `DJANGO_SECRET_KEY` bằng giá trị riêng cho production và đặt `DJANGO_DEBUG=False` khi deploy.

## Thử nghiệm & phát triển
- Giao diện chính: templates trong `core/templates/core/` (ví dụ: dashboard: [core/templates/core/dashboard_student.html](core/templates/core/dashboard_student.html#L1)).
- Logic ghép ca: [core/services.py](core/services.py#L1) — xem hàm `smart_match`, `check_shift_conflict`.

## Git
- Đã thêm file `.gitignore` để loại trừ virtualenv, `.env`, media, IDE files, v.v.

## Hỗ trợ / Tiếp theo
- Muốn mình thêm hướng dẫn deploy (Gunicorn + Nginx), CI/CD, hoặc audit bảo mật cho trường `portal_password` không? Chỉ định mục bạn muốn mình làm tiếp.

---
Last updated: 2026-07-03
