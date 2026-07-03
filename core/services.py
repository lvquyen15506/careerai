"""
Core Business Logic - Services cho Nền tảng Việc làm Sinh viên.

Bao gồm:
- extract_student_code: Trích mã sinh viên từ email @ictu.edu.vn
- smart_match: Thuật toán gợi ý ca phù hợp với lịch rảnh sinh viên
- update_trust_score: Cập nhật điểm uy tín sau mỗi đánh giá
"""
from django.db.models import Q, Avg
from django.utils import timezone


def extract_student_code(email):
    """
    Trích xuất mã sinh viên từ email của các trường Đại học Thái Nguyên.

    Ví dụ: 'dtl2151050001@ictu.edu.vn' -> 'DTL2151050001'

    Args:
        email (str): Địa chỉ email của sinh viên.

    Returns:
        str: Mã sinh viên (viết hoa), hoặc None nếu email không hợp lệ.
    """
    if not email:
        return None
        
    email_lower = email.lower()
    allowed_domains = ['ictu.edu.vn', 'tueba.edu.vn', 'tnut.edu.vn', 'tnus.edu.vn', 'sfl.edu.vn', 'tump.edu.vn', 'tnue.edu.vn', 'tnu.edu.vn']
    
    if not any(email_lower.endswith(f"@{domain}") for domain in allowed_domains):
        return None

    # Mã sinh viên là phần trước dấu @
    student_code = email.split('@')[0].strip().upper()

    if not student_code:
        return None

    return student_code


def check_shift_fits_schedule_helper(shift_start_time, shift_end_time, time_blocks):
    """
    Kiểm tra ca làm có nằm trong danh sách khung giờ rảnh hay không,
    cho phép gộp các khoảng rảnh có khoảng trống nhỏ hơn hoặc bằng 90 phút.
    """
    s_start = shift_start_time.hour * 60 + shift_start_time.minute
    s_end = shift_end_time.hour * 60 + shift_end_time.minute
    
    # Nếu ca làm qua nửa đêm
    crosses_midnight = s_end < s_start
    
    intervals = []
    # Mặc định ca đêm (22:00 - 06:00) luôn được coi là rảnh theo thiết kế giao diện
    intervals.append([1320, 1440])
    intervals.append([0, 360])

    for b in time_blocks:
        b_start = b.start_time.hour * 60 + b.start_time.minute
        b_end = b.end_time.hour * 60 + b.end_time.minute
        
        if b_end < b_start:
            # Ca rảnh qua đêm (vd: 22:00 - 06:00)
            intervals.append([b_start, 1440])
            intervals.append([0, b_end])
        else:
            intervals.append([b_start, b_end])
            
    if not intervals:
        return False
        
    intervals.sort(key=lambda x: x[0])
    
    # Gộp các khoảng rảnh nếu khoảng cách <= 90 phút (bù đắp khoảng trống giữa các buổi rảnh kề nhau)
    merged = []
    for current in intervals:
        if not merged:
            merged.append(list(current))
        else:
            prev = merged[-1]
            if current[0] - prev[1] <= 90:
                prev[1] = max(prev[1], current[1])
            else:
                merged.append(list(current))
                
    if not crosses_midnight:
        for m_start, m_end in merged:
            if m_start <= s_start and m_end >= s_end:
                return True
        return False
    else:
        part1_covered = False
        part2_covered = False
        for m_start, m_end in merged:
            if m_start <= s_start and m_end >= 1440:
                part1_covered = True
            if m_start <= 0 and m_end >= s_end:
                part2_covered = True
        return part1_covered and part2_covered


def check_shift_conflict(student, shift):
    """
    Kiểm tra xem ca làm việc có bị trùng lịch học hoặc lịch thi của sinh viên không.
    Trả về (has_conflict, message)
    """
    from django.utils import timezone
    import datetime
    import re
    
    # 1. Kiểm tra Trùng Lịch Thi (ExamSchedule)
    # Lịch thi có exam_date và exam_time cụ thể.
    # Giả định mỗi ca thi kéo dài 120 phút (2 giờ).
    shift_start_local = timezone.localtime(shift.start_time)
    shift_end_local = timezone.localtime(shift.end_time)
    
    exam_schedules = student.exam_schedules.all()
    for exam in exam_schedules:
        # Chuyển đổi lịch thi thành khoảng thời gian datetime aware
        exam_date = exam.exam_date
        exam_start_t = exam.exam_time
        exam_start_dt = timezone.make_aware(datetime.datetime.combine(exam_date, exam_start_t))
        exam_end_dt = exam_start_dt + datetime.timedelta(hours=2) # 2 tiếng thi
        
        # Kiểm tra giao nhau
        if exam_start_dt < shift.end_time and exam_end_dt > shift.start_time:
            return True, f"Trùng lịch thi học phần: Thi {exam.course_name} vào lúc {exam.exam_time.strftime('%H:%M')} ngày {exam.exam_date.strftime('%d/%m/%Y')}."

    # 2. Kiểm tra Trùng Lịch Học (StudySchedule)
    # Tìm các lịch học học phần trùng thứ trong các ngày mà ca làm bao phủ
    # (Hầu hết ca làm nằm trong 1 ngày, nhưng phòng trường hợp qua đêm)
    start_date = shift_start_local.date()
    end_date = shift_end_local.date()
    
    # Duyệt qua các ngày ca làm diễn ra
    curr_date = start_date
    tiet_map = {
        1: (7, 0, 7, 45),
        2: (7, 50, 8, 35),
        3: (8, 40, 9, 25),
        4: (9, 35, 10, 20),
        5: (10, 25, 11, 10),
        6: (13, 0, 13, 45),
        7: (13, 50, 14, 35),
        8: (14, 40, 15, 25),
        9: (15, 35, 16, 20),
        10: (16, 25, 17, 10),
        11: (18, 0, 18, 45),
        12: (18, 50, 19, 35),
        13: (19, 40, 20, 25),
        14: (20, 30, 21, 15),
    }
    
    while curr_date <= end_date:
        weekday = curr_date.weekday()
        # Lấy các lịch học vào thứ này và trong khoảng ngày hiệu lực của môn học
        schedules = student.study_schedules.filter(
            weekday=weekday
        )
        for sched in schedules:
            if sched.start_date and curr_date < sched.start_date:
                continue
            if sched.end_date and curr_date > sched.end_date:
                continue
            
            # Tính thời gian học dựa trên Tiết học (tiet)
            digits = [int(x) for x in re.findall(r'\d+', str(sched.tiet))]
            if not digits:
                continue
            
            min_tiet = min(digits)
            max_tiet = max(digits)
            
            if min_tiet in tiet_map and max_tiet in tiet_map:
                start_h, start_m, _, _ = tiet_map[min_tiet]
                _, _, end_h, end_m = tiet_map[max_tiet]
                
                class_start_time = datetime.time(start_h, start_m)
                class_end_time = datetime.time(end_h, end_m)
                
                class_start_dt = timezone.make_aware(datetime.datetime.combine(curr_date, class_start_time))
                class_end_dt = timezone.make_aware(datetime.datetime.combine(curr_date, class_end_time))
                
                # Kiểm tra giao nhau
                if class_start_dt < shift.end_time and class_end_dt > shift.start_time:
                    return True, f"Trùng lịch học ĐKTC: Môn {sched.course_name} (Tiết {sched.tiet}) vào ngày {curr_date.strftime('%d/%m/%Y')}."
        
        curr_date += datetime.timedelta(days=1)
        
    return False, ""


def smart_match(student):
    """
    Thuật toán Smart Matching - tìm các ca làm phù hợp 100% với lịch rảnh sinh viên.

    Logic:
    1. Lấy tất cả khung giờ rảnh (TimeBlock) của sinh viên.
    2. Quét tất cả ca làm có status='Open'.
    3. Với mỗi ca, kiểm tra xem ca có nằm hoàn toàn trong khung giờ rảnh
       của sinh viên vào đúng ngày trong tuần đó không.
    4. Trả về danh sách các ca khớp 100%.

    Args:
        student (StudentProfile): Hồ sơ sinh viên cần tìm ca.

    Returns:
        QuerySet: Danh sách JobShift phù hợp, sắp xếp theo thời gian.
    """
    from .models import JobShift, TimeBlock

    # Lấy tất cả khung giờ rảnh của sinh viên
    time_blocks = TimeBlock.objects.filter(student=student)

    if not time_blocks.exists():
        return JobShift.objects.none()

    # Lấy các ca đang mở và chưa đầy khớp với trường và ngành học của sinh viên
    open_shifts = JobShift.objects.filter(
        status='Open',
        start_time__gte=timezone.now()  # Chỉ lấy ca trong tương lai
    ).filter(
        Q(target_school='Tất cả') | Q(target_school__iexact=student.portal_school)
    ).filter(
        Q(target_major='Tất cả') | Q(target_major__iexact=student.major)
    ).select_related('employer')

    matched_shift_ids = []

    for shift in open_shifts:
        # Kiểm tra ca còn chỗ trống
        if not shift.is_available:
            continue

        # Kiểm tra sinh viên chưa ứng tuyển ca này
        if shift.applications.filter(student=student).exists():
            continue

        # Kiểm tra trùng lịch học/thi học phần
        has_conflict, _ = check_shift_conflict(student, shift)
        if has_conflict:
            continue

        # Chuyển đổi sang giờ địa phương để khớp chính xác
        local_start = timezone.localtime(shift.start_time)
        local_end = timezone.localtime(shift.end_time)

        # Lấy ngày trong tuần của ca (0=Monday, 6=Sunday)
        shift_weekday = local_start.weekday()
        shift_start = local_start.time()
        shift_end = local_end.time()
        shift_hour = local_start.hour

        # Kiểm tra nếu ca rơi vào ca đêm (22:00 - 06:00) thì mặc định là rảnh
        is_night_shift = (shift_hour >= 22 or shift_hour < 6)

        if is_night_shift:
            matched_shift_ids.append(shift.id)
        else:
            # Lọc bằng thuật toán gộp khoảng rảnh
            weekday_blocks = time_blocks.filter(weekday=shift_weekday)
            if check_shift_fits_schedule_helper(shift_start, shift_end, weekday_blocks):
                matched_shift_ids.append(shift.id)

    # Trả về QuerySet để dễ phân trang, sắp xếp
    return JobShift.objects.filter(id__in=matched_shift_ids).order_by('start_time')


def update_trust_score(profile, new_rating):
    """
    Cập nhật điểm uy tín động sau mỗi ca làm.

    Công thức: Trung bình cộng tất cả các rating đã nhận.
    Áp dụng cho cả StudentProfile và EmployerProfile.

    Args:
        profile: Instance của StudentProfile hoặc EmployerProfile.
        new_rating (int): Điểm đánh giá mới (1-5), sẽ được quy đổi sang thang 10.

    Returns:
        float: Điểm uy tín mới đã cập nhật.
    """
    from .models import ShiftApplication, StudentProfile, EmployerProfile

    if isinstance(profile, StudentProfile):
        # Tính trung bình tất cả rating từ doanh nghiệp
        avg_rating = ShiftApplication.objects.filter(
            student=profile,
            rating_from_employer__isnull=False
        ).aggregate(avg=Avg('rating_from_employer'))['avg']
    elif isinstance(profile, EmployerProfile):
        # Tính trung bình tất cả rating từ sinh viên
        avg_rating = ShiftApplication.objects.filter(
            shift__employer=profile,
            rating_from_student__isnull=False
        ).aggregate(avg=Avg('rating_from_student'))['avg']
    else:
        return profile.trust_score

    if avg_rating is not None:
        # Quy đổi từ thang 5 sang thang 10
        profile.trust_score = round(avg_rating * 2, 1)
        profile.save(update_fields=['trust_score'])

    return profile.trust_score


def create_timeblocks_from_schedule(student, schedule_data):
    """
    Tạo khung thời gian rảnh (TimeBlock) tự động từ thời khóa biểu học tập.
    
    Quy tắc:
    - Một tuần có 7 ngày (Thứ 2 đến Chủ nhật, weekday từ 0 đến 6).
    - Mỗi ngày chia làm 3 buổi:
      + Sáng (Morning): 07:00:00 - 11:30:00
      + Chiều (Afternoon): 13:00:00 - 17:30:00
      + Tối (Evening): 18:00:00 - 21:30:00
    - Nếu sinh viên có tiết học trùng vào buổi nào thì buổi đó xem như bận (không tạo TimeBlock).
    - Các buổi còn lại không trùng lịch học sẽ tự động được thêm vào TimeBlock rảnh.
    """
    from .models import TimeBlock
    import datetime

    # Xóa lịch rảnh cũ để cập nhật lịch mới
    TimeBlock.objects.filter(student=student).delete()

    # Mảng lưu trạng thái rảnh của từng buổi trong tuần (7 ngày, mỗi ngày 3 buổi: Sáng, Chiều, Tối)
    # Mặc định tất cả các buổi đều rảnh (True)
    free_matrix = {
        w: {'sang': True, 'chieu': True, 'toi': True} for w in range(7)
    }

    # Định nghĩa các buổi dựa trên tiết học
    # Tiết 1-5 -> Sáng
    # Tiết 6-10 -> Chiều
    # Tiết 11+ -> Tối
    for item in schedule_data:
        thu = item.get('thu', '')
        tiet = item.get('tiet', '')
        
        # Chuyển đổi thứ sang weekday index (0-6)
        # Hệ thống scraper trả về thứ từ '2' đến '8' hoặc 'CN'
        weekday = None
        if thu in ['2', '3', '4', '5', '6', '7']:
            weekday = int(thu) - 2
        elif thu in ['8', 'CN', 'chủ nhật', 'Chủ nhật']:
            weekday = 6
        
        if weekday is None or weekday not in free_matrix:
            continue

        # Tìm các tiết học để đánh dấu bận
        tiets = []
        if tiet:
            # Ví dụ: "1-3", "7-9", "1,2,3"
            tiet_str = str(tiet).replace('-', ',')
            parts = [p.strip() for p in tiet_str.split(',') if p.strip().isdigit()]
            if len(parts) == 2 and '-' in str(tiet):
                tiets = list(range(int(parts[0]), int(parts[1]) + 1))
            else:
                tiets = [int(p) for p in parts]

        # Đánh dấu bận theo tiết học
        for t in tiets:
            if 1 <= t <= 5:
                free_matrix[weekday]['sang'] = False
            elif 6 <= t <= 10:
                free_matrix[weekday]['chieu'] = False
            elif t >= 11:
                free_matrix[weekday]['toi'] = False

    # Lưu các block rảnh vào Database
    time_blocks_to_create = []
    
    # Định nghĩa giờ cụ thể cho từng buổi
    blocks_hours = {
        'sang': (datetime.time(7, 0), datetime.time(11, 30)),
        'chieu': (datetime.time(13, 0), datetime.time(17, 30)),
        'toi': (datetime.time(18, 0), datetime.time(21, 30))
    }

    for weekday, sessions in free_matrix.items():
        for session_name, is_free in sessions.items():
            if is_free:
                start_t, end_t = blocks_hours[session_name]
                time_blocks_to_create.append(
                    TimeBlock(
                        student=student,
                        weekday=weekday,
                        start_time=start_t,
                        end_time=end_t
                    )
                )

    if time_blocks_to_create:
        TimeBlock.objects.bulk_create(time_blocks_to_create)


def fetch_and_sync_student_profile(student, password, school):
    """
    Gọi scraper để lấy thông tin từ ĐKTC và đồng bộ vào profile sinh viên.
    Lưu credentials và tự động tạo lịch rảnh từ lịch học.
    """
    from .scrapers import scrape_student_data
    from .models import StudySchedule
    import datetime
    
    # Thực hiện cào dữ liệu sinh viên
    data = scrape_student_data(student.student_code, password, school)
    
    # Lưu credentials nếu thành công
    if school:
        student.portal_school = school
    if password:
        student.portal_password = password
        
    # Đồng bộ họ tên sinh viên nếu trong DB chưa có hoặc đang mặc định
    update_fields = ['portal_school', 'portal_password']
    if data.get('full_name') and (not student.full_name or student.full_name == student.student_code):
        student.full_name = data['full_name']
        student.is_profile_complete = True
        update_fields.extend(['full_name', 'is_profile_complete'])
        
    if data.get('major'):
        student.major = data['major']
        update_fields.append('major')
        
    if data.get('class_name'):
        student.class_name = data['class_name']
        update_fields.append('class_name')
        
    student.save(update_fields=update_fields)
        
    # Tự động đồng bộ thời khóa biểu thành lịch rảnh và lưu vào DB
    schedule = data.get('schedule', [])
    # Xóa lịch học cũ
    StudySchedule.objects.filter(student=student).delete()
    
    schedules_to_create = []
    for item in schedule:
        thu = item.get('thu', '')
        tiet = item.get('tiet', '')
        
        # Chuyển đổi thứ sang index (0-6)
        weekday = None
        if thu in ['2', '3', '4', '5', '6', '7']:
            weekday = int(thu) - 2
        elif thu in ['8', 'CN', 'chủ nhật', 'Chủ nhật']:
            weekday = 6
            
        if weekday is None:
            continue
            
        start_date = None
        if item.get('start_date'):
            try:
                start_date = datetime.datetime.strptime(item['start_date'], '%Y-%m-%d').date()
            except Exception:
                pass
        end_date = None
        if item.get('end_date'):
            try:
                end_date = datetime.datetime.strptime(item['end_date'], '%Y-%m-%d').date()
            except Exception:
                pass
                
        schedules_to_create.append(
            StudySchedule(
                student=student,
                course_code=item.get('ma_hoc_phan') or '',
                course_name=item.get('ten_hoc_phan') or '',
                credits=item.get('so_tc') or '',
                lop=item.get('lop') or '',
                weekday=weekday,
                tiet=tiet,
                phong=item.get('phong') or '',
                start_date=start_date,
                end_date=end_date,
                giang_vien=item.get('giang_vien') or '',
                link_meet=item.get('link_meet') or '',
            )
        )
    if schedules_to_create:
        StudySchedule.objects.bulk_create(schedules_to_create)
        
    create_timeblocks_from_schedule(student, schedule)
        
    # Tự động đồng bộ lịch thi
    exams = data.get('exams', [])
    if exams:
        from .models import ExamSchedule
        ExamSchedule.objects.filter(student=student).delete()
        
        exams_to_create = []
        for item in exams:
            exam_date = None
            if item.get('exam_date'):
                try:
                    exam_date = datetime.datetime.strptime(item['exam_date'], '%Y-%m-%d').date()
                except Exception:
                    pass
            
            exam_time = None
            if item.get('exam_time'):
                try:
                    exam_time = datetime.datetime.strptime(item['exam_time'], '%H:%M').time()
                except Exception:
                    pass
            
            if exam_date and exam_time:
                exams_to_create.append(
                    ExamSchedule(
                        student=student,
                        course_code=item.get('course_code') or '',
                        course_name=item.get('course_name') or '',
                        exam_date=exam_date,
                        exam_time=exam_time,
                        room=item.get('room') or '',
                        exam_format=item.get('exam_format') or 'Trắc nghiệm',
                        sbd=item.get('sbd') or '',
                        notes=item.get('notes') or ''
                    )
                )
        if exams_to_create:
            ExamSchedule.objects.bulk_create(exams_to_create)
        
    return data

