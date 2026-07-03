# YÊU CẦU DỰ ÁN: NỀN TẢNG AI KẾT NỐI & QUẢN TRỊ VIỆC LÀM SINH VIÊN

## 1. Vai trò & Mục tiêu
Bạn là một Senior Full-Stack Developer chuyên về Python/Django. Nhiệm vụ của bạn là viết toàn bộ mã nguồn (codebase) cho dự án "Nền tảng AI kết nối và quản trị việc làm sinh viên" dựa trên tài liệu thiết kế dưới đây. 
Hãy viết code chuẩn production, tuân thủ PEP8, có comment giải thích rõ ràng và xử lý lỗi đầy đủ.

## 2. Công nghệ sử dụng (Tech Stack)
* **Backend:** Framework Django (Kiến trúc MVT).
* **Database:** MySQL (Sử dụng Foreign Keys để đảm bảo toàn vẹn dữ liệu).
* **Authentication:** `django-allauth` (Cấu hình SSO qua Google/Microsoft, chỉ cho phép email đuôi `@ictu.edu.vn`).
* **Frontend:** Django Templates + Bootstrap 5 (Responsive Design).

## 3. Thiết kế Cơ sở dữ liệu (Database Schema / ERD)
Cấu trúc mở rộng từ bảng `User` mặc định của Django:

1.  **`auth_user`**: Bảng mặc định của Django (id, username, email, password, is_active).
2.  **`student_profile`** (1-1 với `auth_user`):
    * `user_id` (OneToOneField)
    * `student_code` (Mã SV trích xuất từ email)
    * `full_name`, `class_name` (Lớp sinh hoạt), `major` (Ngành học)
    * `trust_score` (Float, mặc định 5.0)
3.  **`employer_profile`** (1-1 với `auth_user`):
    * `user_id` (OneToOneField)
    * `company_name`, `address`, `business_license`
    * `is_verified` (Boolean, mặc định False)
    * `trust_score` (Float, mặc định 5.0)
4.  **`job_shift`** (1-N từ `employer_profile`):
    * `employer_id` (ForeignKey)
    * `title`
    * `start_time` (DateTime), `end_time` (DateTime)
    * `wage_per_hour` (Decimal)
    * `required_students` (Integer)
    * `status` (Choices: Open, Filled, Closed)
5.  **`shift_application`** (1-N từ `job_shift` và 1-N từ `student_profile`):
    * `shift_id` (ForeignKey), `student_id` (ForeignKey)
    * `status` (Choices: Pending, CheckIn, CheckOut, Completed)
    * `check_in_time` (DateTime, null=True), `check_out_time` (DateTime, null=True)
    * `rating_from_employer` (Integer, null=True), `rating_from_student` (Integer, null=True)

## 4. Các Luồng Logic Cốt lõi (Core Business Logic)
* **Xác thực SSO:** Khóa đăng nhập chỉ dành cho `@ictu.edu.vn`. Lần đầu đăng nhập sinh viên phải bổ sung thông tin (Lớp, Ngành) và thời gian rảnh (Time-blocks).
* **Smart Matching:** Thuật toán (viết trong `services.py` hoặc QuerySet) quét các ca làm `Open`, đối chiếu với lịch rảnh của sinh viên để gợi ý ca khớp 100% thời gian.
* **Check-in/Check-out:** Sinh viên nhận ca -> Check-in -> Check-out. Doanh nghiệp duyệt chấm công.
* **Trust Score:** Cập nhật điểm uy tín động sau mỗi ca làm dựa trên đánh giá sao (1-5).

---

## 5. KẾ HOẠCH TRIỂN KHAI (EXECUTION PLAN) - QUAN TRỌNG
Để tránh việc code bị cắt ngang do giới hạn output, hãy thực hiện dự án này theo từng Giai đoạn (Phase). 
**Bây giờ, hãy chỉ viết code cho Giai đoạn 1. Khi bạn xong, tôi sẽ nói "Tiếp tục" để bạn làm Giai đoạn 2.**

* **Giai đoạn 1: Cấu hình Khởi tạo.** Viết `requirements.txt` và toàn bộ nội dung file `settings.py` (Cấu hình MySQL, django-allauth, static/templates).
* **Giai đoạn 2: Database Models.** Viết toàn bộ file `models.py` và `admin.py` (để quản trị viên kiểm duyệt doanh nghiệp).
* **Giai đoạn 3: Core Logic (Services & Authentication).** Viết file `services.py` chứa logic trích xuất mã sinh viên từ email, thuật toán Smart Matching và tính toán Trust Score.
* **Giai đoạn 4: Views & URLs.** Viết `views.py` và `urls.py` xử lý các API/luồng cho Đăng nhập, Tạo ca làm, Nhận ca, Check-in/out.
* **Giai đoạn 5: Frontend Templates.** Viết cấu trúc HTML/Bootstrap 5 cơ bản cho các màn hình: Dashboard Sinh viên, Dashboard Doanh nghiệp.
