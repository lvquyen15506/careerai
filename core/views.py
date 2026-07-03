"""
Views cho Nền tảng Việc làm Sinh viên.

Bao gồm các view chính:
- HomeView: Trang chủ / chuyển hướng theo role
- CompleteProfileView: Bổ sung thông tin lần đầu
- StudentDashboardView: Dashboard sinh viên
- EmployerDashboardView: Dashboard doanh nghiệp
- CreateShiftView: Tạo ca làm
- ShiftDetailView: Chi tiết ca + Check-in/out
- ApplyShiftView: Sinh viên nhận ca
- CheckInView / CheckOutView: Chấm công
- RateView: Đánh giá sau ca làm
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponseForbidden
from django.db import models

from .models import (
    StudentProfile,
    EmployerProfile,
    JobShift,
    ShiftApplication,
    TimeBlock,
)
from .forms import (
    StudentProfileForm,
    AutoSyncProfileForm,
    EmployerProfileForm,
    JobShiftForm,
    TimeBlockForm,
    RatingForm,
)
from .services import smart_match, update_trust_score, fetch_and_sync_student_profile


def health_check_view(request):
    """Simple health endpoint for load balancers / Render health checks."""
    from django.http import HttpResponse
    return HttpResponse('OK', content_type='text/plain')


def home_view(request):
    """
    Trang chủ - chuyển hướng theo vai trò nếu đã đăng nhập,
    ngược lại hiển thị Landing Page công khai.
    """
    user = request.user

    if not user.is_authenticated:
        return render(request, 'core/landing.html')

    # Nếu là Admin/Staff
    if user.is_staff or user.is_superuser:
        return redirect('admin_dashboard')

    # Kiểm tra là doanh nghiệp
    if hasattr(user, 'employer_profile'):
        return redirect('employer_dashboard')

    # Kiểm tra là sinh viên
    if hasattr(user, 'student_profile'):
        if not user.student_profile.is_profile_complete:
            return redirect('complete_profile')
        return redirect('student_dashboard')

    # Chưa có profile -> tạo mới
    return redirect('complete_profile')


@login_required
def complete_profile_view(request):
    """
    Quản lý lịch rảnh và thời khóa biểu của sinh viên.
    """
    user = request.user
    if user.is_staff or hasattr(user, 'employer_profile'):
        return redirect('home')

    try:
        profile = user.student_profile
    except StudentProfile.DoesNotExist:
        from .services import extract_student_code
        student_code = extract_student_code(user.email) or user.username
        profile = StudentProfile.objects.create(
            user=user,
            student_code=student_code,
            full_name=user.get_full_name() or '',
        )

    # Nếu chưa hoàn thiện thông tin cơ bản, chuyển hướng sang trang Settings
    if not profile.is_profile_complete:
        messages.info(request, 'ℹ️ Vui lòng cập nhật thông tin cá nhân và ảnh đại diện trước.')
        return redirect('student_settings')

    sync_form = AutoSyncProfileForm(initial={'school': profile.portal_school or 'ictu'})
    time_block_form = TimeBlockForm() # Không dùng prefix để đồng bộ với add_time_block_view

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'auto_sync':
            sync_form = AutoSyncProfileForm(request.POST)
            if sync_form.is_valid():
                school = sync_form.cleaned_data['school']
                pwd = sync_form.cleaned_data['portal_password'] or profile.portal_password
                
                # Cập nhật trường portal_school
                if school:
                    profile.portal_school = school
                    profile.save(update_fields=['portal_school'])

                if not pwd:
                    messages.error(request, '❌ Vui lòng nhập mật khẩu ĐKTC cho lần đồng bộ đầu tiên.')
                else:
                    try:
                        from .services import fetch_and_sync_student_profile
                        fetch_and_sync_student_profile(profile, pwd, school)
                        messages.success(request, '✅ Đồng bộ thông tin và thời khóa biểu từ ĐKTC thành công!')
                        return redirect('complete_profile')
                    except Exception as e:
                        messages.error(request, f'❌ Đồng bộ thất bại: {str(e)}')

    existing_blocks = TimeBlock.objects.filter(student=profile)
    
    # Tính ngày tháng của tuần hiện tại để hiển thị bên cạnh thứ
    import datetime
    from django.utils import timezone
    today = timezone.localdate()
    monday_of_this_week = today - datetime.timedelta(days=today.weekday())
    week_dates = [monday_of_this_week + datetime.timedelta(days=i) for i in range(7)]
    for block in existing_blocks:
        if 0 <= block.weekday < 7:
            block.calendar_date = week_dates[block.weekday].strftime('%d/%m')
        else:
            block.calendar_date = ''

    return render(request, 'core/complete_profile.html', {
        'time_block_form': time_block_form,
        'sync_form': sync_form,
        'existing_blocks': existing_blocks,
        'profile': profile,
    })


@login_required
def student_settings_view(request):
    """
    Cài đặt thông tin cá nhân và ảnh đại diện của sinh viên.
    """
    user = request.user
    if user.is_staff or hasattr(user, 'employer_profile'):
        return redirect('home')

    try:
        profile = user.student_profile
    except StudentProfile.DoesNotExist:
        from .services import extract_student_code
        student_code = extract_student_code(user.email) or user.username
        profile = StudentProfile.objects.create(
            user=user,
            student_code=student_code,
            full_name=user.get_full_name() or '',
        )

    if request.method == 'POST':
        form = StudentProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.is_profile_complete = True
            profile.save()
            messages.success(request, '✅ Cập nhật thông tin cá nhân và ảnh đại diện thành công!')
            return redirect('student_settings')
    else:
        form = StudentProfileForm(instance=profile)

    return render(request, 'core/settings_student.html', {
        'form': form,
        'profile': profile,
    })


@login_required
def student_profile_view(request):
    """
    Trang xem hồ sơ cá nhân của sinh viên.
    """
    user = request.user
    if user.is_staff or hasattr(user, 'employer_profile'):
        return redirect('home')

    try:
        profile = user.student_profile
    except StudentProfile.DoesNotExist:
        return redirect('complete_profile')

    return render(request, 'core/profile_student.html', {
        'profile': profile,
    })



@login_required
def student_dashboard_view(request):
    """
    Dashboard Sinh viên:
    - Danh sách ca gợi ý (Smart Matching)
    - Danh sách ca đã nhận
    - Lịch sử ca đã hoàn thành
    - Ma trận thời gian rảnh (grid_data)
    """
    user = request.user

    if not hasattr(user, 'student_profile'):
        if user.is_staff or hasattr(user, 'employer_profile'):
            return redirect('home')
        return redirect('complete_profile')

    profile = user.student_profile

    # Smart Match - gợi ý ca phù hợp
    suggested_shifts = smart_match(profile)

    # Ca đã nhận (đang hoạt động)
    active_applications = ShiftApplication.objects.filter(
        student=profile,
        status__in=['Pending', 'CheckIn']
    ).select_related('shift', 'shift__employer')

    # Lịch sử ca đã hoàn thành
    completed_applications = ShiftApplication.objects.filter(
        student=profile,
        status__in=['CheckOut', 'Completed']
    ).select_related('shift', 'shift__employer').order_by('-applied_at')[:10]

    # Tính toán ma trận lịch tích hợp (Timeline Grid: Học, Rảnh, Làm)
    import datetime
    from django.utils import timezone
    
    try:
        week_offset = int(request.GET.get('week_offset', 0))
    except ValueError:
        week_offset = 0

    today = timezone.localdate()
    monday_of_this_week = today - datetime.timedelta(days=today.weekday())
    target_monday = monday_of_this_week + datetime.timedelta(weeks=week_offset)
    
    week_dates = []
    for i in range(7):
        week_dates.append(target_monday + datetime.timedelta(days=i))

    weekday_labels = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN']
    formatted_headers = []
    for idx, d in enumerate(week_dates):
        formatted_headers.append({
            'label': weekday_labels[idx],
            'date_str': d.strftime('%d/%m')
        })

    from .models import StudySchedule
    study_schedules = StudySchedule.objects.filter(student=profile)
    time_blocks = TimeBlock.objects.filter(student=profile)
    
    # Tất cả ca làm việc của sinh viên (chờ duyệt, đã check-in, hoàn thành,...)
    applied_shifts = ShiftApplication.objects.filter(
        student=profile,
        status__in=['Pending', 'CheckIn', 'CheckOut', 'Completed']
    ).select_related('shift', 'shift__employer')

    sessions = ['sang', 'chieu', 'toi', 'dem']
    session_info = {
        'sang': {'label': 'Sáng', 'time': '07:00 - 11:30'},
        'chieu': {'label': 'Chiều', 'time': '13:00 - 17:30'},
        'toi': {'label': 'Tối', 'time': '18:00 - 21:30'},
        'dem': {'label': 'Đêm', 'time': '22:00 - 06:00'}
    }

    timeline_grid = {}
    for sess in sessions:
        timeline_grid[sess] = []
        for day_idx in range(7):
            day_date = week_dates[day_idx]
            is_past = day_date < today
            if sess == 'dem':
                timeline_grid[sess].append({
                    'type': 'free',
                    'label': 'Rảnh',
                    'details': '22:00 - 06:00',
                    'is_past': is_past,
                    'date_str': day_date.strftime('%Y-%m-%d'),
                    'date_dmy': day_date.strftime('%d/%m/%Y'),
                    'weekday_label': weekday_labels[day_idx],
                    'session': sess
                })
            else:
                timeline_grid[sess].append({
                    'type': 'busy',
                    'label': 'Bận',
                    'details': '',
                    'is_past': is_past,
                    'date_str': day_date.strftime('%Y-%m-%d'),
                    'date_dmy': day_date.strftime('%d/%m/%Y'),
                    'weekday_label': weekday_labels[day_idx],
                    'session': sess
                })

    # 1. Điền lịch rảnh (TimeBlocks) vào ma trận
    for tb in time_blocks:
        sess = None
        start_hour = tb.start_time.hour
        if 6 <= start_hour < 12:
            sess = 'sang'
        elif 12 <= start_hour < 18:
            sess = 'chieu'
        elif 18 <= start_hour < 22:
            sess = 'toi'
        else:
            sess = 'dem'
            
        if sess in timeline_grid and 0 <= tb.weekday < 7:
            is_past = timeline_grid[sess][tb.weekday]['is_past']
            day_date = week_dates[tb.weekday]
            timeline_grid[sess][tb.weekday] = {
                'type': 'free',
                'label': 'Rảnh',
                'details': f'{tb.start_time.strftime("%H:%M")}-{tb.end_time.strftime("%H:%M")}',
                'is_past': is_past,
                'date_str': day_date.strftime('%Y-%m-%d'),
                'date_dmy': day_date.strftime('%d/%m/%Y'),
                'weekday_label': weekday_labels[tb.weekday],
                'session': sess
            }

    # 2. Điền lịch học (StudySchedule) vào ma trận (đè lên lịch rảnh/bận)
    for sched in study_schedules:
        date_item = week_dates[sched.weekday]
        if sched.start_date and date_item < sched.start_date:
            continue
        if sched.end_date and date_item > sched.end_date:
            continue

        import re
        tiet_match = re.search(r'\d+', str(sched.tiet))
        sess = None
        if tiet_match:
            t = int(tiet_match.group())
            if 1 <= t <= 5:
                sess = 'sang'
            elif 6 <= t <= 10:
                sess = 'chieu'
            elif 11 <= t <= 13:
                sess = 'toi'
            else:
                sess = 'dem'
        else:
            sess = 'toi'
                
        if sess in timeline_grid and 0 <= sched.weekday < 7:
            is_past = timeline_grid[sess][sched.weekday]['is_past']
            timeline_grid[sess][sched.weekday] = {
                'type': 'class',
                'label': f'Học: {sched.course_name}',
                'details': f'Tiết {sched.tiet} | {sched.phong}',
                'code': sched.course_code,
                'credits': sched.credits,
                'lop': sched.lop,
                'weekday': sched.weekday,
                'tiet': sched.tiet,
                'room': sched.phong,
                'start_date': sched.start_date.strftime('%d/%m/%Y') if sched.start_date else '',
                'end_date': sched.end_date.strftime('%d/%m/%Y') if sched.end_date else '',
                'giang_vien': sched.giang_vien,
                'link_meet': sched.link_meet,
                'is_past': is_past
            }

    # 3. Điền ca làm việc (ShiftApplication) vào ma trận (đè lên nếu có ca làm việc)
    for app in applied_shifts:
        shift = app.shift
        shift_local_date = timezone.localdate(shift.start_time)
        if shift_local_date in week_dates:
            day_idx = week_dates.index(shift_local_date)
            
            local_start = timezone.localtime(shift.start_time)
            local_end = timezone.localtime(shift.end_time)
            
            start_hour = local_start.hour
            sess = None
            if 6 <= start_hour < 12:
                sess = 'sang'
            elif 12 <= start_hour < 18:
                sess = 'chieu'
            elif 18 <= start_hour < 22:
                sess = 'toi'
            else:
                sess = 'dem'
                
            if sess in timeline_grid:
                status_text = app.get_status_display()
                is_past = timeline_grid[sess][day_idx]['is_past']
                timeline_grid[sess][day_idx] = {
                    'type': 'shift',
                    'label': f'Làm: {shift.title}',
                    'details': f'{local_start.strftime("%H:%M")}-{local_end.strftime("%H:%M")}',
                    'company': shift.employer.company_name,
                    'status': app.status,
                    'status_display': status_text,
                    'shift_id': shift.id,
                    'wage': f'{shift.wage_per_hour:,.0f}',
                    'is_past': is_past
                }

    # 4. Điền lịch thi (ExamSchedule) vào ma trận (đè lên các lịch khác)
    from .models import ExamSchedule
    exams = ExamSchedule.objects.filter(
        student=profile,
        exam_date__in=week_dates
    )
    for exam in exams:
        day_idx = week_dates.index(exam.exam_date)
        exam_hour = exam.exam_time.hour
        
        sess = None
        if 6 <= exam_hour < 12:
            sess = 'sang'
        elif 12 <= exam_hour < 18:
            sess = 'chieu'
        elif 18 <= exam_hour < 22:
            sess = 'toi'
        else:
            sess = 'dem'
            
        if sess in timeline_grid:
            is_past = timeline_grid[sess][day_idx]['is_past']
            timeline_grid[sess][day_idx] = {
                'type': 'exam',
                'label': f'Thi: {exam.course_name}',
                'details': f'{exam.exam_time.strftime("%H:%M")} | Phòng {exam.room}',
                'code': exam.course_code,
                'room': exam.room,
                'format': exam.exam_format,
                'sbd': exam.sbd,
                'notes': exam.notes,
                'date': exam.exam_date.strftime('%d/%m/%Y'),
                'time': exam.exam_time.strftime('%H:%M'),
                'is_past': is_past
            }

    # Đóng gói dữ liệu để đưa vào context dưới dạng list có thứ tự buổi
    formatted_grid = []
    for sess in sessions:
        formatted_grid.append({
            'session': sess,
            'label': session_info[sess]['label'],
            'time': session_info[sess]['time'],
            'days': timeline_grid[sess]
        })

    # ------------------- DATA FOR TÌM CA LÀM VIỆC -------------------
    from django.db.models import Q
    shifts = JobShift.objects.filter(
        status='Open',
        start_time__gte=timezone.now()
    ).filter(
        Q(target_school='Tất cả') | Q(target_school__iexact=profile.portal_school)
    ).filter(
        Q(target_major='Tất cả') | Q(target_major__iexact=profile.major)
    ).select_related('employer')
    
    # Lọc search
    q = request.GET.get('q', '')
    if q:
        shifts = shifts.filter(
            Q(title__icontains=q) | 
            Q(employer__company_name__icontains=q)
        )
    # Lọc lương
    min_wage = request.GET.get('min_wage', '')
    if min_wage:
        try:
            shifts = shifts.filter(wage_per_hour__gte=int(min_wage))
        except ValueError:
            pass

    # Lọc trùng lịch học/thi
    from .services import check_shift_conflict
    valid_shifts = []
    for s in shifts:
        has_conflict, _ = check_shift_conflict(profile, s)
        if not has_conflict:
            valid_shifts.append(s)

    applied_shift_ids = ShiftApplication.objects.filter(
        student=profile
    ).values_list('shift_id', flat=True)

    # ------------------- DATA FOR LỊCH RẢNH & TKB -------------------
    existing_blocks = TimeBlock.objects.filter(student=profile)
    for block in existing_blocks:
        if 0 <= block.weekday < 7:
            block.calendar_date = week_dates[block.weekday].strftime('%d/%m')
        else:
            block.calendar_date = ''
            
    sync_form = AutoSyncProfileForm(initial={'school': profile.portal_school or 'ictu'})
    time_block_form = TimeBlockForm()

    # ------------------- DATA FOR LỊCH THI -------------------
    exams = ExamSchedule.objects.filter(student=profile).order_by('exam_date', 'exam_time')

    return render(request, 'core/dashboard_student.html', {
        'profile': profile,
        'suggested_shifts': suggested_shifts,
        'active_applications': active_applications,
        'completed_applications': completed_applications,
        'grid_data': formatted_grid,
        'week_offset': week_offset,
        'prev_offset': week_offset - 1,
        'next_offset': week_offset + 1,
        'formatted_headers': formatted_headers,
        'shifts': valid_shifts,
        'applied_shift_ids': list(applied_shift_ids),
        'q': q,
        'min_wage': min_wage,
        'existing_blocks': existing_blocks,
        'sync_form': sync_form,
        'time_block_form': time_block_form,
        'exams': exams,
        'is_student_dashboard': True,
    })


@login_required
def find_shifts_view(request):
    """
    Tìm ca làm việc:
    - Hiển thị danh sách tất cả các ca làm đang mở (Open)
    - Cho phép tìm kiếm theo tiêu đề hoặc tên doanh nghiệp
    - Lọc theo mức lương tối thiểu
    """
    user = request.user
    if not hasattr(user, 'student_profile'):
        if user.is_staff or hasattr(user, 'employer_profile'):
            return redirect('home')
        return redirect('complete_profile')
        
    profile = user.student_profile
    if not profile.is_profile_complete:
        return redirect('complete_profile')

    from django.utils import timezone
    from django.db.models import Q
    # Query open shifts (chỉ lấy ca trong tương lai và khớp với trường/ngành sinh viên)
    shifts = JobShift.objects.filter(
        status='Open',
        start_time__gte=timezone.now()
    ).filter(
        Q(target_school='Tất cả') | Q(target_school__iexact=profile.portal_school)
    ).filter(
        Q(target_major='Tất cả') | Q(target_major__iexact=profile.major)
    ).select_related('employer')
    
    # Filter search query
    q = request.GET.get('q', '')
    if q:
        shifts = shifts.filter(
            models.Q(title__icontains=q) | 
            models.Q(employer__company_name__icontains=q)
        )
        
    # Filter min wage
    min_wage = request.GET.get('min_wage', '')
    if min_wage:
        try:
            shifts = shifts.filter(wage_per_hour__gte=int(min_wage))
        except ValueError:
            pass

    # Lọc bỏ các ca trùng lịch học/thi học phần
    from .services import check_shift_conflict
    valid_shifts = []
    for s in shifts:
        has_conflict, _ = check_shift_conflict(profile, s)
        if not has_conflict:
            valid_shifts.append(s)

    applied_shift_ids = ShiftApplication.objects.filter(
        student=profile
    ).values_list('shift_id', flat=True)

    return render(request, 'core/find_shifts.html', {
        'profile': profile,
        'shifts': valid_shifts,
        'q': q,
        'min_wage': min_wage,
        'applied_shift_ids': list(applied_shift_ids),
    })


@login_required
def ajax_find_shifts_view(request):
    """
    API tìm ca làm việc trống vào khung giờ đã chọn cho sinh viên chọn nhanh
    """
    from django.http import JsonResponse
    from django.urls import reverse
    from django.db.models import Q
    import datetime

    date_str = request.GET.get('date', '')       # YYYY-MM-DD
    session_name = request.GET.get('session', '') # sang, chieu, toi, dem

    if not date_str or not session_name:
        return JsonResponse({'shifts': []})

    try:
        target_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'shifts': []})

    if not hasattr(request.user, 'student_profile'):
        return JsonResponse({'shifts': []})

    profile = request.user.student_profile
    filter_free = request.GET.get('filter_free', 'true') == 'true'

    # Lấy khung giờ rảnh của sinh viên vào ngày này
    from .models import TimeBlock
    weekday = target_date.weekday()
    time_blocks = TimeBlock.objects.filter(student=profile, weekday=weekday) if filter_free else None

    # Lấy tất cả ca làm Open trên hệ thống khớp với trường và ngành học của sinh viên
    open_shifts = JobShift.objects.filter(
        status='Open',
        start_time__date=target_date
    ).filter(
        Q(target_school='Tất cả') | Q(target_school__iexact=profile.portal_school)
    ).filter(
        Q(target_major='Tất cả') | Q(target_major__iexact=profile.major)
    ).select_related('employer')

    filtered_shifts = []
    for s in open_shifts:
        local_start = timezone.localtime(s.start_time)
        local_end = timezone.localtime(s.end_time)
        hour = local_start.hour
        match = False

        if session_name == 'sang' and 6 <= hour < 12:
            match = True
        elif session_name == 'chieu' and 12 <= hour < 18:
            match = True
        elif session_name == 'toi' and 18 <= hour < 22:
            match = True
        elif session_name == 'dem' and (hour >= 22 or hour < 6):
            match = True

        if match:
            # Lọc bỏ các ca trùng lịch học/thi học phần
            from .services import check_shift_conflict
            has_conflict, _ = check_shift_conflict(profile, s)
            if has_conflict:
                continue

            # Lọc theo lịch rảnh
            if filter_free and time_blocks is not None:
                is_night_shift = (hour >= 22 or hour < 6)
                if not is_night_shift:
                    from .services import check_shift_fits_schedule_helper
                    shift_start = local_start.time()
                    shift_end = local_end.time()
                    
                    if not check_shift_fits_schedule_helper(shift_start, shift_end, time_blocks):
                        continue
            # Check status ứng tuyển
            app = ShiftApplication.objects.filter(student=profile, shift=s).first()
            applied = app is not None
            status_display = app.get_status_display() if app else ""

            filtered_shifts.append({
                'id': s.id,
                'title': s.title,
                'company': s.employer.company_name,
                'wage': f'{s.wage_per_hour:,.0f}',
                'start_time': local_start.strftime('%H:%M'),
                'end_time': timezone.localtime(s.end_time).strftime('%H:%M'),
                'applied': applied,
                'status_display': status_display,
                'apply_url': reverse('apply_shift', args=[s.id]),
                'detail_url': reverse('shift_detail', args=[s.id]),
            })

    return JsonResponse({'shifts': filtered_shifts})


@login_required
def exam_schedule_view(request):
    """
    Hiển thị lịch thi của sinh viên.
    """
    user = request.user
    if not hasattr(user, 'student_profile'):
        if user.is_staff or hasattr(user, 'employer_profile'):
            return redirect('home')
        return redirect('complete_profile')
        
    profile = user.student_profile
    if not profile.is_profile_complete:
        return redirect('complete_profile')

    from .models import ExamSchedule
    exams = ExamSchedule.objects.filter(student=profile).order_by('exam_date', 'exam_time')

    return render(request, 'core/exam_schedule.html', {
        'profile': profile,
        'exams': exams,
    })


@login_required
def employer_dashboard_view(request):
    """
    Dashboard Doanh nghiệp:
    - Danh sách ca đã tạo
    - Đơn ứng tuyển cần duyệt chấm công
    - Thống kê số ca theo trạng thái
    - Chỉ số phân tích (Analytics)
    """
    user = request.user

    if not hasattr(user, 'employer_profile'):
        return HttpResponseForbidden('Bạn không có quyền truy cập trang này.')

    profile = user.employer_profile

    # Danh sách ca đã tạo
    my_shifts = JobShift.objects.filter(
        employer=profile
    ).prefetch_related('applications__student').order_by('-created_at')

    # Đơn cần duyệt chấm công (status=CheckOut, chờ đánh giá)
    pending_reviews = ShiftApplication.objects.filter(
        shift__employer=profile,
        status='CheckOut'
    ).select_related('shift', 'student')

    # Thống kê số lượng ca làm theo trạng thái
    open_shifts_count = my_shifts.filter(status='Open').count()
    filled_shifts_count = my_shifts.filter(status='Filled').count()
    closed_shifts_count = my_shifts.filter(status='Closed').count()

    # Thống kê phân tích mới (Analytics)
    total_shifts = my_shifts.count()
    active_students_count = ShiftApplication.objects.filter(
        shift__employer=profile,
        status__in=['Pending', 'CheckIn']
    ).values('student').distinct().count()

    completed_or_checkout_apps = ShiftApplication.objects.filter(
        shift__employer=profile,
        status__in=['CheckOut', 'Completed']
    ).select_related('shift')
    total_budget = 0
    for app in completed_or_checkout_apps:
        shift = app.shift
        effective_start = max(app.check_in_time, shift.start_time) if app.check_in_time else shift.start_time
        effective_end = min(app.check_out_time, shift.end_time) if app.check_out_time else shift.end_time
        duration_hours = (effective_end - effective_start).total_seconds() / 3600.0
        if duration_hours < 0:
            duration_hours = 0.0
        total_budget += duration_hours * float(shift.wage_per_hour)

    avg_rating = ShiftApplication.objects.filter(
        shift__employer=profile,
        rating_from_student__isnull=False
    ).aggregate(models.Avg('rating_from_student'))['rating_from_student__avg']
    if avg_rating is None:
        avg_rating = 5.0

    # Lấy danh sách ứng viên (workers)
    from django.db.models import Count, Avg, Q
    workers = StudentProfile.objects.filter(
        applications__shift__employer=profile
    ).annotate(
        total_shifts=Count('applications', filter=Q(applications__shift__employer=profile)),
        completed_shifts=Count('applications', filter=Q(applications__shift__employer=profile, applications__status='Completed')),
        avg_rating=Avg('applications__rating_from_employer', filter=Q(applications__shift__employer=profile))
    ).distinct()

    return render(request, 'core/dashboard_employer.html', {
        'profile': profile,
        'my_shifts': my_shifts,
        'pending_reviews': pending_reviews,
        'open_shifts_count': open_shifts_count,
        'filled_shifts_count': filled_shifts_count,
        'closed_shifts_count': closed_shifts_count,
        'total_shifts': total_shifts,
        'active_students_count': active_students_count,
        'total_budget': total_budget,
        'avg_rating': avg_rating,
        'now': timezone.now(),
        'workers': workers,
        'is_employer_dashboard': True,
        'form': JobShiftForm(),
    })


@login_required
def create_shift_view(request):
    """Doanh nghiệp tạo ca làm mới."""
    user = request.user
    if not hasattr(user, 'employer_profile'):
        return HttpResponseForbidden('Chỉ doanh nghiệp mới có thể tạo ca làm.')

    if not user.employer_profile.is_verified:
        messages.warning(request, '⚠️ Tài khoản doanh nghiệp chưa được xác minh. Vui lòng chờ admin duyệt.')
        return redirect('employer_dashboard')

    if request.method == 'POST':
        form = JobShiftForm(request.POST)
        if form.is_valid():
            shift = form.save(commit=False)
            shift.employer = user.employer_profile
            shift.save()
            messages.success(request, f'✅ Ca làm "{shift.title}" đã được tạo thành công!')
            return redirect('/employer/dashboard/?tab=tab-employer-dashboard')
    else:
        form = JobShiftForm()

    return render(request, 'core/create_shift.html', {
        'form': form,
    })


@login_required
def edit_shift_view(request, shift_id):
    """Sửa thông tin ca làm việc - dành cho doanh nghiệp sở hữu."""
    shift = get_object_or_404(JobShift, id=shift_id)
    user = request.user
    
    is_owner = hasattr(user, 'employer_profile') and shift.employer == user.employer_profile
    if not is_owner:
        return HttpResponseForbidden('Bạn không có quyền chỉnh sửa ca làm này.')
        
    if shift.end_time < timezone.now():
        messages.error(request, '❌ Ca làm đã kết thúc, không thể chỉnh sửa.')
        return redirect('shift_detail', shift_id=shift.id)
        
    if request.method == 'POST':
        form = JobShiftForm(request.POST, instance=shift)
        if form.is_valid():
            form.save()
            messages.success(request, f'✅ Ca làm "{shift.title}" đã được cập nhật thành công!')
            return redirect('/employer/dashboard/?tab=tab-employer-dashboard')
    else:
        form = JobShiftForm(instance=shift)
        
    return render(request, 'core/edit_shift.html', {
        'form': form,
        'shift': shift,
        'is_admin': False,
        'is_expired': shift.end_time < timezone.now(),
    })


@login_required
def delete_shift_view(request, shift_id):
    """Xóa ca làm việc - dành cho doanh nghiệp sở hữu."""
    shift = get_object_or_404(JobShift, id=shift_id)
    user = request.user
    
    is_owner = hasattr(user, 'employer_profile') and shift.employer == user.employer_profile
    if not is_owner:
        return HttpResponseForbidden('Bạn không có quyền xóa ca làm này.')
        
    if shift.end_time < timezone.now():
        messages.error(request, '❌ Ca làm đã kết thúc, không thể xóa.')
        return redirect('shift_detail', shift_id=shift.id)
        
    shift.delete()
    messages.success(request, '❌ Đã xóa ca làm việc thành công!')
    return redirect('/employer/dashboard/?tab=tab-employer-dashboard')


@login_required
def admin_create_shift_view(request):
    """Admin tạo ca làm mới cho doanh nghiệp."""
    user = request.user
    is_admin = user.is_staff or user.is_superuser

    if not is_admin:
        return HttpResponseForbidden('Chỉ quản trị viên mới có thể thực hiện thao tác này.')

    employers = EmployerProfile.objects.filter(is_verified=True)

    if request.method == 'POST':
        form = JobShiftForm(request.POST)
        employer_id = request.POST.get('employer')
        if not employer_id:
            form.add_error(None, 'Vui lòng chọn doanh nghiệp tuyển dụng.')

        if form.is_valid():
            shift = form.save(commit=False)
            employer = get_object_or_404(EmployerProfile, id=employer_id)
            shift.employer = employer
            shift.save()
            messages.success(request, f'✅ Ca làm "{shift.title}" đã được tạo thành công!')
            return redirect('/portal-admin/overview/?tab=tab-shifts')
    else:
        form = JobShiftForm()

    return render(request, 'core/admin_create_shift.html', {
        'form': form,
        'employers': employers,
        'active_tab': 'tab-shifts',
    })


@login_required
def admin_edit_shift_view(request, shift_id):
    """Admin chỉnh sửa ca làm việc."""
    user = request.user
    is_admin = user.is_staff or user.is_superuser

    if not is_admin:
        return HttpResponseForbidden('Chỉ quản trị viên mới có thể thực hiện thao tác này.')

    shift = get_object_or_404(JobShift, id=shift_id)

    if request.method == 'POST':
        form = JobShiftForm(request.POST, instance=shift)
        if form.is_valid():
            form.save()
            messages.success(request, f'✅ Ca làm "{shift.title}" đã được cập nhật thành công!')
            return redirect('/portal-admin/overview/?tab=tab-shifts')
    else:
        form = JobShiftForm(instance=shift)

    return render(request, 'core/admin_edit_shift.html', {
        'form': form,
        'shift': shift,
        'is_admin': True,
        'is_expired': shift.end_time < timezone.now(),
        'active_tab': 'tab-shifts',
    })


@login_required
def admin_delete_shift_view(request, shift_id):
    """Admin xóa ca làm việc."""
    user = request.user
    is_admin = user.is_staff or user.is_superuser

    if not is_admin:
        return HttpResponseForbidden('Chỉ quản trị viên mới có thể thực hiện thao tác này.')

    shift = get_object_or_404(JobShift, id=shift_id)
    shift.delete()
    messages.success(request, '❌ Đã xóa ca làm việc thành công!')
    return redirect('/portal-admin/overview/?tab=tab-shifts')


@login_required
def shift_detail_view(request, shift_id):
    """Chi tiết ca làm - hiển thị khác nhau cho SV và DN/Admin."""
    shift = get_object_or_404(JobShift, id=shift_id)
    user = request.user
    application = None
    
    is_employer = hasattr(user, 'employer_profile')
    is_admin = user.is_staff or user.is_superuser
    is_owner = False

    if is_employer:
        is_owner = (shift.employer == user.employer_profile)
        # BẢO MẬT: Nhà tuyển dụng chỉ được xem ca làm của chính mình tạo ra
        if not is_owner and not is_admin:
            return HttpResponseForbidden('Bạn không có quyền truy cập thông tin ca làm của doanh nghiệp khác.')

    # Lấy danh sách đơn ứng tuyển nếu là chủ sở hữu hoặc admin
    if is_owner or is_admin:
        applications = shift.applications.select_related('student').all()
    else:
        applications = None

    # Kiểm tra nếu sinh viên đã ứng tuyển
    if hasattr(user, 'student_profile'):
        application = ShiftApplication.objects.filter(
            shift=shift,
            student=user.student_profile
        ).first()

    if is_admin:
        import django.utils.timezone as tz
        return render(request, 'core/admin_shift_detail.html', {
            'shift': shift,
            'application': application,
            'is_employer': False,
            'is_admin': True,
            'is_owner': False,
            'applications': applications,
            'now': tz.now(),
            'active_tab': 'tab-shifts',
        })
    elif is_employer:
        return render(request, 'core/shift_detail_employer.html', {
            'shift': shift,
            'application': application,
            'is_employer': True,
            'is_admin': False,
            'is_owner': is_owner,
            'applications': applications,
        })
    else:
        return render(request, 'core/shift_detail_student.html', {
            'shift': shift,
            'application': application,
            'is_employer': is_employer,
            'applications': applications,
        })


@login_required
def apply_shift_view(request, shift_id):
    """Sinh viên nhận ca làm."""
    shift = get_object_or_404(JobShift, id=shift_id)
    user = request.user

    if not hasattr(user, 'student_profile'):
        messages.error(request, '❌ Bạn cần có hồ sơ sinh viên để nhận ca.')
        return redirect('home')

    now = timezone.now()
    if shift.registration_deadline and now > shift.registration_deadline:
        messages.error(request, '❌ Đã hết hạn đăng ký ca làm này.')
        return redirect('shift_detail', shift_id=shift_id)

    if not shift.is_available:
        messages.warning(request, '⚠️ Ca làm này đã đầy hoặc đã đóng.')
        return redirect('shift_detail', shift_id=shift_id)

    # Kiểm tra chưa ứng tuyển
    existing = ShiftApplication.objects.filter(
        shift=shift,
        student=user.student_profile
    ).exists()

    if existing:
        messages.info(request, 'ℹ️ Bạn đã ứng tuyển ca này rồi.')
    else:
        # Kiểm tra trùng lịch học/thi học phần
        from .services import check_shift_conflict
        has_conflict, conflict_msg = check_shift_conflict(user.student_profile, shift)
        if has_conflict:
            messages.error(request, f"❌ Không thể nhận ca: {conflict_msg}")
            return redirect('shift_detail', shift_id=shift_id)

        ShiftApplication.objects.create(
            shift=shift,
            student=user.student_profile,
            status='Pending'
        )
        # Kiểm tra nếu đã đủ người
        if shift.accepted_count >= shift.required_students:
            shift.status = 'Filled'
            shift.save()

        messages.success(request, f'✅ Bạn đã nhận ca "{shift.title}" thành công!')

    return redirect('shift_detail', shift_id=shift_id)


@login_required
def check_in_view(request, application_id):
    """Sinh viên check-in ca làm."""
    application = get_object_or_404(ShiftApplication, id=application_id)
    user = request.user

    if not hasattr(user, 'student_profile') or application.student != user.student_profile:
        return HttpResponseForbidden('Bạn không có quyền check-in ca này.')

    if application.status != 'Pending':
        messages.warning(request, '⚠️ Không thể check-in. Trạng thái hiện tại không hợp lệ.')
        return redirect('shift_detail', shift_id=application.shift.id)

    now = timezone.now()
    shift = application.shift
    
    import datetime
    late_limit = shift.start_time + datetime.timedelta(hours=1)
    if now > late_limit:
        messages.error(request, '❌ Bạn đã trễ hạn check-in (tối đa 1 tiếng sau khi ca bắt đầu).')
        return redirect('shift_detail', shift_id=shift.id)

    application.status = 'CheckIn'
    application.check_in_time = now
    application.save()

    messages.success(request, '✅ Check-in thành công!')
    return redirect('shift_detail', shift_id=application.shift.id)


@login_required
def check_out_view(request, application_id):
    """Sinh viên check-out ca làm."""
    application = get_object_or_404(ShiftApplication, id=application_id)
    user = request.user

    if not hasattr(user, 'student_profile') or application.student != user.student_profile:
        return HttpResponseForbidden('Bạn không có quyền check-out ca này.')

    if application.status != 'CheckIn':
        messages.warning(request, '⚠️ Bạn cần check-in trước khi check-out.')
        return redirect('shift_detail', shift_id=application.shift.id)

    now = timezone.now()
    shift = application.shift
    
    import datetime
    allowed_time = shift.end_time - datetime.timedelta(minutes=30)
    if now < allowed_time:
        messages.error(request, '❌ Bạn chỉ được check-out tối đa 30 phút trước khi ca làm kết thúc.')
        return redirect('shift_detail', shift_id=shift.id)

    application.status = 'CheckOut'
    application.check_out_time = now
    application.save()

    messages.success(request, '✅ Check-out thành công! Chờ doanh nghiệp duyệt chấm công.')
    return redirect('shift_detail', shift_id=application.shift.id)


@login_required
def rate_view(request, application_id):
    """
    Đánh giá sau ca làm.
    - Sinh viên đánh giá doanh nghiệp (rating_from_student)
    - Doanh nghiệp đánh giá sinh viên (rating_from_employer) + duyệt Completed
    """
    application = get_object_or_404(ShiftApplication, id=application_id)
    user = request.user

    if request.method == 'POST':
        form = RatingForm(request.POST)
        if form.is_valid():
            rating = form.cleaned_data['rating']

            # Doanh nghiệp hoặc Admin đánh giá sinh viên
            is_employer_owner = hasattr(user, 'employer_profile') and application.shift.employer == user.employer_profile
            is_admin = user.is_staff or user.is_superuser
            
            if is_employer_owner or is_admin:
                application.rating_from_employer = rating
                
                status_choice = request.POST.get('status', 'Completed')
                if status_choice not in ['Completed', 'Failed']:
                    status_choice = 'Completed'
                application.status = status_choice
                application.save()

                # Cập nhật trust_score sinh viên
                update_trust_score(application.student, rating)

                messages.success(request, f'✅ Đã đánh giá sinh viên và duyệt {application.get_status_display().lower()}!')
                return redirect('admin_dashboard' if is_admin else 'employer_dashboard')

            # Sinh viên đánh giá doanh nghiệp
            elif hasattr(user, 'student_profile') and application.student == user.student_profile:
                application.rating_from_student = rating
                application.save()

                # Cập nhật trust_score doanh nghiệp
                update_trust_score(application.shift.employer, rating)

                messages.success(request, '✅ Cảm ơn bạn đã đánh giá!')
                return redirect('student_dashboard')

            else:
                return HttpResponseForbidden('Bạn không có quyền đánh giá.')
    else:
        form = RatingForm()

    is_admin = user.is_staff or user.is_superuser
    if is_admin:
        base_template = 'core/base.html'
    else:
        base_template = 'core/base.html' if hasattr(user, 'employer_profile') else 'core/base_student.html'
    return render(request, 'core/rate.html', {
        'form': form,
        'application': application,
        'base_template': base_template,
    })


@login_required
def add_time_block_view(request):
    """Sinh viên thêm hoặc sửa khung giờ rảnh."""
    if not hasattr(request.user, 'student_profile'):
        if request.user.is_staff or hasattr(request.user, 'employer_profile'):
            return redirect('home')
        return redirect('complete_profile')

    if request.method == 'POST':
        block_id = request.POST.get('block_id')
        if block_id:
            from .models import TimeBlock
            block = get_object_or_404(TimeBlock, id=block_id, student=request.user.student_profile)
            form = TimeBlockForm(request.POST, instance=block)
            if form.is_valid():
                form.save()
                messages.success(request, '✅ Đã cập nhật khung giờ rảnh!')
        else:
            form = TimeBlockForm(request.POST)
            if form.is_valid():
                block = form.save(commit=False)
                block.student = request.user.student_profile
                block.save()
                messages.success(request, '✅ Đã thêm khung giờ rảnh!')
    return redirect('complete_profile')


@login_required
def delete_time_block_view(request, block_id):
    """Sinh viên xóa khung giờ rảnh."""
    block = get_object_or_404(TimeBlock, id=block_id)
    if hasattr(request.user, 'student_profile') and block.student == request.user.student_profile:
        block.delete()
        messages.success(request, '✅ Đã xóa khung giờ rảnh!')
    
    if not hasattr(request.user, 'student_profile') and (request.user.is_staff or hasattr(request.user, 'employer_profile')):
        return redirect('home')
    return redirect('complete_profile')


def register_employer_view(request):
    """Doanh nghiệp đăng ký tài khoản."""
    if request.user.is_authenticated and hasattr(request.user, 'employer_profile'):
        return redirect('employer_dashboard')

    if request.method == 'POST':
        form = EmployerProfileForm(request.POST)
        if form.is_valid():
            if request.user.is_authenticated:
                employer = form.save(commit=False)
                employer.user = request.user
                employer.save()
                messages.success(
                    request,
                    '✅ Đăng ký doanh nghiệp thành công! Vui lòng chờ admin xác minh.'
                )
                return redirect('employer_dashboard')
            else:
                email = request.POST.get('email', '').strip()
                password = request.POST.get('password')
                
                if not email or not password:
                    messages.error(request, '❌ Vui lòng điền đầy đủ email và mật khẩu tài khoản.')
                    return render(request, 'core/register_employer.html', {'form': form})
                
                from django.contrib.auth.models import User
                # Kiểm tra email tồn tại
                if User.objects.filter(email=email).exists() or User.objects.filter(username=email).exists():
                    messages.error(request, '❌ Email đăng ký đã tồn tại trong hệ thống.')
                    return render(request, 'core/register_employer.html', {'form': form})
                
                # Tạo user
                username = email.split('@')[0]
                base_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1
                
                user = User.objects.create_user(username=username, email=email, password=password)
                
                employer = form.save(commit=False)
                employer.user = user
                employer.save()
                
                # Đăng nhập tự động
                from django.contrib.auth import login as django_login
                django_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                
                messages.success(
                    request,
                    '✅ Đăng ký tài khoản doanh nghiệp thành công! Vui lòng chờ admin xác minh.'
                )
                return redirect('employer_dashboard')
    else:
        form = EmployerProfileForm()

    return render(request, 'core/register_employer.html', {
        'form': form,
    })


def unified_login_view(request):
    """
    Trang đăng nhập duy nhất cho tất cả các loại tài khoản:
    - Vai trò: Sinh viên (đồng bộ ĐKTC trường hoặc dùng tài khoản hệ thống)
    - Vai trò: Doanh nghiệp / Khác (xác thực local DB)
    """
    from django.contrib.auth import authenticate, login as django_login
    from django.contrib.auth.models import User

    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        role = request.POST.get('role', 'student')
        school = request.POST.get('school', 'local')
        username_or_email = request.POST.get('username', '').strip()
        password = request.POST.get('password')

        if not username_or_email or not password:
            messages.error(request, '❌ Vui lòng điền đầy đủ thông tin đăng nhập.')
            return render(request, 'account/login.html')

        # 1. Đăng nhập với vai trò Sinh viên qua cổng ĐKTC Trường
        if role == 'student' and school != 'local':
            student_code = username_or_email.upper()
            try:
                from .scrapers import scrape_student_data
                data = scrape_student_data(student_code, password, school)
                
                email = f"{student_code.lower()}@{school}.edu.vn"
                
                # Tìm user hiện tại
                user = User.objects.filter(username=student_code).first()
                if not user:
                    user = User.objects.filter(email=email).first()
                    
                if not user:
                    user = User.objects.create(
                        username=student_code,
                        email=email,
                        first_name=data.get('full_name', '')[:30]
                    )
                    user.set_unusable_password()
                    user.save()

                # Đồng bộ Profile
                student_profile, created = StudentProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'student_code': student_code,
                        'full_name': data.get('full_name') or student_code,
                        'is_profile_complete': True
                    }
                )
                
                update_fields = []
                if data.get('full_name') and student_profile.full_name != data['full_name']:
                    student_profile.full_name = data['full_name']
                    student_profile.is_profile_complete = True
                    update_fields.extend(['full_name', 'is_profile_complete'])

                if data.get('major') and student_profile.major != data['major']:
                    student_profile.major = data['major']
                    update_fields.append('major')

                if data.get('class_name') and student_profile.class_name != data['class_name']:
                    student_profile.class_name = data['class_name']
                    update_fields.append('class_name')

                if update_fields:
                    student_profile.save(update_fields=update_fields)

                # Đồng bộ thời khóa biểu sang lịch rảnh
                schedule = data.get('schedule', [])
                from .services import create_timeblocks_from_schedule
                create_timeblocks_from_schedule(student_profile, schedule)

                django_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, f"🎉 Đăng nhập thành công sinh viên: {student_profile.full_name}!")
                return redirect('student_dashboard')

            except Exception as e:
                messages.error(request, f"❌ Đăng nhập ĐKTC thất bại: {str(e)}")
                return render(request, 'account/login.html')

        # 2. Đăng nhập hệ thống (Doanh nghiệp, Admin, hoặc Sinh viên dùng tài khoản hệ thống)
        else:
            user = None
            if '@' in username_or_email:
                user = User.objects.filter(email=username_or_email).first()
            if not user:
                user = User.objects.filter(username=username_or_email).first()

            if user:
                authenticated_user = authenticate(username=user.username, password=password)
                if authenticated_user:
                    # Kiểm tra khớp vai trò nếu cần (nếu doanh nghiệp chọn nhầm tab sinh viên)
                    if role == 'employer' and not hasattr(authenticated_user, 'employer_profile') and not authenticated_user.is_staff:
                        messages.error(request, '❌ Tài khoản này không phải là tài khoản Doanh nghiệp.')
                        return render(request, 'account/login.html')
                    
                    django_login(request, authenticated_user)
                    messages.success(request, f"Chào mừng {authenticated_user.get_full_name() or authenticated_user.username} quay trở lại!")
                    return redirect('home')

            messages.error(request, '❌ Tài khoản hoặc mật khẩu hệ thống không chính xác.')

    return render(request, 'account/login.html')



@login_required
def refresh_schedule_view(request):
    """
    Sinh viên yêu cầu làm mới thời khóa biểu từ cổng ĐKTC để cập nhật lại lịch rảnh.
    Hỗ trợ cả POST (khi nhập mới) và GET/POST (khi dùng thông tin lưu sẵn).
    """
    if not hasattr(request.user, 'student_profile'):
        return redirect('home')

    student = request.user.student_profile
    
    # Lấy thông tin từ POST, nếu trống thì lấy từ database
    school = request.POST.get('school') or student.portal_school
    password = request.POST.get('password') or student.portal_password

    if not school or not password:
        messages.error(request, '❌ Không tìm thấy thông tin đăng nhập ĐKTC. Vui lòng cung cấp mật khẩu.')
        return redirect('student_dashboard')

    try:
        from .services import fetch_and_sync_student_profile
        fetch_and_sync_student_profile(student, password, school)
        messages.success(request, '🔄 Cập nhật lịch học và làm mới lịch rảnh thành công!')
    except Exception as e:
        messages.error(request, f'❌ Cập nhật lịch học thất bại: {str(e)}')

    return redirect('student_dashboard')


@login_required
def admin_dashboard_view(request):
    """
    Bảng quản trị hệ thống CareerAI (Admin Overview):
    - Thống kê tổng số người dùng
    - Thống kê số đơn ứng tuyển / Khớp nối thành công
    - Thống kê tổng tiền giao dịch (lương)
    - Duyệt giấy phép kinh doanh của Doanh nghiệp
    - Quản lý danh sách sinh viên, doanh nghiệp
    - Khớp ca thủ công cho sinh viên và doanh nghiệp
    """
    if not request.user.is_staff:
        return HttpResponseForbidden('Bạn không có quyền truy cập trang quản trị.')

    from django.contrib.auth.models import User
    active_users_count = User.objects.count()
    matches_today_count = ShiftApplication.objects.count()
    
    # Tính tổng tiền giao dịch của tất cả ca làm việc được khớp
    all_apps = ShiftApplication.objects.all().select_related('shift')
    total_revenue = 0
    for app in all_apps:
        shift = app.shift
        if app.status in ['CheckOut', 'Completed']:
            effective_start = max(app.check_in_time, shift.start_time) if app.check_in_time else shift.start_time
            effective_end = min(app.check_out_time, shift.end_time) if app.check_out_time else shift.end_time
            duration = (effective_end - effective_start).total_seconds() / 3600.0
            if duration < 0:
                duration = 0.0
        elif app.status == 'Failed':
            duration = 0.0
        else:
            duration = (shift.end_time - shift.start_time).total_seconds() / 3600.0
        total_revenue += float(shift.wage_per_hour) * duration

    # 1. Thống kê theo khối ngành của sinh viên (dựa trên đơn ứng tuyển)
    from django.db.models import Q
    cntt_q = Q(student__major__icontains='CNTT') | Q(student__major__icontains='công nghệ thông tin') | Q(student__major__icontains='tin học')
    kinhte_q = Q(student__major__icontains='kinh tế') | Q(student__major__icontains='kế toán') | Q(student__major__icontains='quản trị') | Q(student__major__icontains='tài chính')
    kythuat_q = Q(student__major__icontains='kỹ thuật') | Q(student__major__icontains='điện') | Q(student__major__icontains='cơ khí') | Q(student__major__icontains='công nghệ')
    supham_q = Q(student__major__icontains='sư phạm') | Q(student__major__icontains='giáo dục') | Q(student__major__icontains='ngôn ngữ') | Q(student__major__icontains='tiếng')
    yduoc_q = Q(student__major__icontains='y') | Q(student__major__icontains='dược') | Q(student__major__icontains='điều dưỡng')

    cntt_count = ShiftApplication.objects.filter(cntt_q).count()
    kinhte_count = ShiftApplication.objects.filter(kinhte_q).count()
    kythuat_count = ShiftApplication.objects.filter(kythuat_q).count()
    supham_count = ShiftApplication.objects.filter(supham_q).count()
    yduoc_count = ShiftApplication.objects.filter(yduoc_q).count()

    max_count = max(cntt_count, kinhte_count, kythuat_count, supham_count, yduoc_count, 1)
    cntt_h = int((cntt_count / max_count) * 90) or 5
    kinhte_h = int((kinhte_count / max_count) * 90) or 5
    kythuat_h = int((kythuat_count / max_count) * 90) or 5
    supham_h = int((supham_count / max_count) * 90) or 5
    yduoc_h = int((yduoc_count / max_count) * 90) or 5

    # 2. Thống kê theo lĩnh vực công việc (phân loại qua tiêu đề ca)
    fb_q = Q(shift__title__icontains='phục vụ') | Q(shift__title__icontains='bán hàng') | Q(shift__title__icontains='thu ngân') | Q(shift__title__icontains='pha chế') | Q(shift__title__icontains='quán') | Q(shift__title__icontains='cafe')
    retail_q = Q(shift__title__icontains='tư vấn') | Q(shift__title__icontains='tuyển sinh') | Q(shift__title__icontains='giao hàng') | Q(shift__title__icontains='shipper') | Q(shift__title__icontains='telesale') | Q(shift__title__icontains='kho')
    tech_q = Q(shift__title__icontains='it') | Q(shift__title__icontains='kỹ thuật') | Q(shift__title__icontains='mạng') | Q(shift__title__icontains='bảo trì') | Q(shift__title__icontains='an ninh') | Q(shift__title__icontains='guard')

    fb_count = ShiftApplication.objects.filter(fb_q).count()
    retail_count = ShiftApplication.objects.filter(retail_q).count()
    tech_count = ShiftApplication.objects.filter(tech_q).count()

    total_sectors = fb_count + retail_count + tech_count
    if total_sectors > 0:
        fb_pct = int((fb_count / total_sectors) * 100)
        retail_pct = int((retail_count / total_sectors) * 100)
        tech_pct = 100 - fb_pct - retail_pct
    else:
        fb_pct, retail_pct, tech_pct = 40, 30, 30

    fb_deg = int((fb_pct / 100) * 360)
    retail_deg = fb_deg + int((retail_pct / 100) * 360)

    # Danh sách doanh nghiệp chờ kiểm duyệt
    pending_employers = EmployerProfile.objects.filter(is_verified=False).select_related('user')

    # Danh sách sinh viên và doanh nghiệp phục vụ quản lý
    students = StudentProfile.objects.all().select_related('user')
    employers = EmployerProfile.objects.all().select_related('user')

    # Danh sách ca làm việc đang mở để khớp ca thủ công (chưa hết hạn và chưa đủ người)
    import django.utils.timezone as tz
    now = tz.now()
    raw_open_shifts = JobShift.objects.filter(status='Open', end_time__gt=now).select_related('employer')
    open_shifts = [s for s in raw_open_shifts if s.accepted_count < s.required_students]

    # Danh sách tất cả ca làm phục vụ quản lý
    all_shifts = JobShift.objects.all().select_related('employer').prefetch_related('applications').order_by('-created_at')

    all_applications = ShiftApplication.objects.all().select_related('student', 'shift__employer').order_by('-id')

    return render(request, 'core/admin_dashboard.html', {
        'active_users_count': active_users_count,
        'matches_today_count': matches_today_count,
        'total_revenue': total_revenue,
        'pending_employers': pending_employers,
        'students': students,
        'employers': employers,
        'open_shifts': open_shifts,
        'all_shifts': all_shifts,
        'now': now,
        'all_applications': all_applications,
        'cntt_h': cntt_h,
        'kinhte_h': kinhte_h,
        'kythuat_h': kythuat_h,
        'supham_h': supham_h,
        'yduoc_h': yduoc_h,
        'fb_pct': fb_pct,
        'retail_pct': retail_pct,
        'tech_pct': tech_pct,
        'fb_deg': fb_deg,
        'retail_deg': retail_deg,
        'total_sectors': total_sectors,
        'is_admin_dashboard': True,
        'form': JobShiftForm(),
    })


@login_required
def manual_match_view(request):
    """Admin thực hiện khớp ca thủ công giữa Sinh viên và Ca làm việc."""
    if not request.user.is_staff:
        return HttpResponseForbidden('Bạn không có quyền thực hiện thao tác này.')

    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        shift_id = request.POST.get('shift_id')

        if not student_id or not shift_id:
            messages.error(request, '❌ Vui lòng chọn đầy đủ Sinh viên và Ca làm.')
            return redirect('admin_dashboard')

        student = get_object_or_404(StudentProfile, id=student_id)
        shift = get_object_or_404(JobShift, id=shift_id)

        if not shift.is_available:
            messages.warning(request, f'⚠️ Ca làm "{shift.title}" đã đầy hoặc đã đóng.')
            return redirect('admin_dashboard')

        # Kiểm tra trùng lặp khớp ca
        existing = ShiftApplication.objects.filter(shift=shift, student=student).exists()
        if existing:
            messages.info(request, f'ℹ️ Sinh viên {student.full_name} đã ứng tuyển/khớp ca này.')
        else:
            # Tạo đơn khớp ca
            ShiftApplication.objects.create(
                shift=shift,
                student=student,
                status='Pending'
            )
            # Cập nhật trạng thái ca nếu đầy
            if shift.accepted_count >= shift.required_students:
                shift.status = 'Filled'
                shift.save()
            messages.success(request, f'✅ Đã khớp ca thành công cho SV: {student.full_name} vào ca: {shift.title}!')

    return redirect('admin_dashboard')


@login_required
def verify_employer_view(request, employer_id):
    """Duyệt hoặc từ chối doanh nghiệp liên kết."""
    if not request.user.is_staff:
        return HttpResponseForbidden('Chỉ admin mới có quyền thực hiện thao tác này.')

    employer = get_object_or_404(EmployerProfile, id=employer_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            employer.is_verified = True
            employer.save()
            messages.success(request, f'✅ Đã phê duyệt doanh nghiệp: {employer.company_name}!')
        elif action == 'reject':
            company_name = employer.company_name
            employer.delete()
            messages.success(request, f'❌ Đã từ chối và xóa hồ sơ doanh nghiệp: {company_name}.')

    return redirect('admin_dashboard')


@login_required
def admin_delete_student_view(request, student_id):
    """Admin xóa tài khoản sinh viên."""
    if not request.user.is_staff:
        return HttpResponseForbidden('Bạn không có quyền thực hiện.')
    student = get_object_or_404(StudentProfile, id=student_id)
    user = student.user
    full_name = student.full_name
    student.delete()
    user.delete()
    messages.success(request, f'❌ Đã xóa tài khoản sinh viên: {full_name}.')
    return redirect('admin_dashboard')


@login_required
def admin_delete_employer_view(request, employer_id):
    """Admin xóa tài khoản doanh nghiệp."""
    if not request.user.is_staff:
        return HttpResponseForbidden('Bạn không có quyền thực hiện.')
    employer = get_object_or_404(EmployerProfile, id=employer_id)
    user = employer.user
    company_name = employer.company_name
    employer.delete()
    user.delete()
    messages.success(request, f'❌ Đã xóa tài khoản doanh nghiệp: {company_name}.')
    return redirect('admin_dashboard')


@login_required
def admin_edit_student_view(request, student_id):
    """Admin sửa thông tin tài khoản sinh viên."""
    if not request.user.is_staff:
        return HttpResponseForbidden('Bạn không có quyền thực hiện.')
    student = get_object_or_404(StudentProfile, id=student_id)
    if request.method == 'POST':
        student.full_name = request.POST.get('full_name')
        student.student_code = request.POST.get('student_code')
        student.class_name = request.POST.get('class_name')
        student.major = request.POST.get('major')
        try:
            student.trust_score = float(request.POST.get('trust_score', 5.0))
        except ValueError:
            pass
        student.save()
        messages.success(request, f'✅ Đập nhật thông tin sinh viên {student.full_name} thành công!')
    return redirect('admin_dashboard')


@login_required
def admin_edit_employer_view(request, employer_id):
    """Admin sửa thông tin doanh nghiệp."""
    if not request.user.is_staff:
        return HttpResponseForbidden('Bạn không có quyền thực hiện.')
    employer = get_object_or_404(EmployerProfile, id=employer_id)
    if request.method == 'POST':
        employer.company_name = request.POST.get('company_name')
        employer.business_license = request.POST.get('business_license')
        employer.address = request.POST.get('address')
        try:
            employer.trust_score = float(request.POST.get('trust_score', 5.0))
        except ValueError:
            pass
        employer.is_verified = request.POST.get('is_verified') == 'true' or 'is_verified' in request.POST
        employer.save()
        messages.success(request, f'✅ Cập nhật thông tin doanh nghiệp {employer.company_name} thành công!')
    return redirect('admin_dashboard')


@login_required
def admin_create_student_view(request):
    """Admin thêm tài khoản sinh viên mới."""
    if not request.user.is_staff:
        return HttpResponseForbidden('Bạn không có quyền thực hiện.')
    if request.method == 'POST':
        from django.contrib.auth.models import User
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        full_name = request.POST.get('full_name')
        student_code = request.POST.get('student_code')
        class_name = request.POST.get('class_name')
        major = request.POST.get('major')

        if User.objects.filter(username=username).exists():
            messages.error(request, '❌ Tên tài khoản đã tồn tại.')
            return redirect('admin_dashboard')
        if User.objects.filter(email=email).exists():
            messages.error(request, '❌ Email đã tồn tại.')
            return redirect('admin_dashboard')
        if StudentProfile.objects.filter(student_code=student_code).exists():
            messages.error(request, '❌ Mã sinh viên đã tồn tại.')
            return redirect('admin_dashboard')

        user = User.objects.create_user(username=username, email=email, password=password)
        StudentProfile.objects.create(
            user=user,
            student_code=student_code,
            full_name=full_name,
            class_name=class_name,
            major=major,
            is_profile_complete=True
        )
        messages.success(request, f'✅ Đã thêm tài khoản sinh viên: {full_name}!')
    return redirect('admin_dashboard')


@login_required
def admin_create_employer_view(request):
    """Admin thêm tài khoản doanh nghiệp mới."""
    if not request.user.is_staff:
        return HttpResponseForbidden('Bạn không có quyền thực hiện.')
    if request.method == 'POST':
        from django.contrib.auth.models import User
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        company_name = request.POST.get('company_name')
        business_license = request.POST.get('business_license')
        address = request.POST.get('address')

        if User.objects.filter(username=username).exists():
            messages.error(request, '❌ Tên tài khoản đã tồn tại.')
            return redirect('admin_dashboard')
        if User.objects.filter(email=email).exists():
            messages.error(request, '❌ Email đã tồn tại.')
            return redirect('admin_dashboard')

        user = User.objects.create_user(username=username, email=email, password=password)
        EmployerProfile.objects.create(
            user=user,
            company_name=company_name,
            business_license=business_license,
            address=address,
            is_verified=True
        )
        messages.success(request, f'✅ Đã thêm doanh nghiệp tuyển dụng: {company_name}!')
    return redirect('admin_dashboard')


@login_required
def admin_delete_application_view(request, application_id):
    """Admin hủy khớp ca/đơn ứng tuyển của sinh viên."""
    if not request.user.is_staff:
        return HttpResponseForbidden('Bạn không có quyền thực hiện.')
    app = get_object_or_404(ShiftApplication, id=application_id)
    shift = app.shift
    student_name = app.student.full_name
    shift_title = shift.title
    app.delete()
    
    if shift.status == 'Filled' and shift.accepted_count < shift.required_students:
        shift.status = 'Open'
        shift.save()
        
    messages.success(request, f'❌ Đã hủy khớp ca làm cho SV {student_name} khỏi ca "{shift_title}".')
    return redirect('admin_dashboard')


@login_required
def employer_student_profile_view(request, student_id):
    """Doanh nghiệp xem hồ sơ chi tiết của sinh viên và lịch sử ca làm."""
    user = request.user
    if not hasattr(user, 'employer_profile'):
        return HttpResponseForbidden('Bạn không có quyền truy cập trang này.')
        
    student = get_object_or_404(StudentProfile, id=student_id)
    
    # Lấy lịch sử ca làm hoàn thành của sinh viên này
    completed_jobs = ShiftApplication.objects.filter(
        student=student,
        status='Completed'
    ).select_related('shift', 'shift__employer').order_by('-check_out_time')
    
    return render(request, 'core/employer_student_profile.html', {
        'student': student,
        'completed_jobs': completed_jobs,
        'profile': user.employer_profile,
    })


@login_required
def employer_cancel_application_view(request, application_id):
    """Doanh nghiệp từ chối / hủy đăng ký ca làm của sinh viên."""
    user = request.user
    if not hasattr(user, 'employer_profile'):
        return HttpResponseForbidden('Bạn không có quyền thực hiện thao tác này.')
        
    application = get_object_or_404(ShiftApplication, id=application_id)
    if application.shift.employer != user.employer_profile:
        return HttpResponseForbidden('Bạn không quản lý ca làm này.')
        
    shift = application.shift
    student_name = application.student.full_name
    
    application.delete()
    
    # Cập nhật lại trạng thái ca làm nếu ca đang Filled -> Open
    if shift.status == 'Filled':
        shift.status = 'Open'
        shift.save()
        
    messages.success(request, f'❌ Đã hủy đăng ký ca làm của sinh viên {student_name}.')
    return redirect('shift_detail', shift_id=shift.id)


@login_required
def employer_export_csv_view(request):
    """Doanh nghiệp xuất báo cáo chấm công ra file CSV."""
    user = request.user
    if not hasattr(user, 'employer_profile'):
        return HttpResponseForbidden('Chỉ doanh nghiệp mới có quyền xuất báo cáo.')
        
    profile = user.employer_profile
    
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="bao_cao_cham_cong_{profile.company_name}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Tên Ca Làm', 'Ngày Làm', 'Thời Gian Bắt Đầu', 'Thời Gian Kết Thúc',
        'Sinh Viên', 'Mã Sinh Viên', 'Lớp Sinh Hoạt', 'Lương/Giờ (VNĐ)', 
        'Tổng Giờ Làm (Giờ)', 'Tổng Lương Nhận (VNĐ)', 'Đánh Giá Của DN', 'Trạng Thái'
    ])
    
    applications = ShiftApplication.objects.filter(
        shift__employer=profile
    ).select_related('shift', 'student').order_by('-applied_at')
    
    for app in applications:
        shift = app.shift
        if app.status in ['CheckOut', 'Completed']:
            effective_start = max(app.check_in_time, shift.start_time) if app.check_in_time else shift.start_time
            effective_end = min(app.check_out_time, shift.end_time) if app.check_out_time else shift.end_time
            duration = (effective_end - effective_start).total_seconds() / 3600.0
            if duration < 0:
                duration = 0.0
        else:
            duration = 0.0
        total_wage = duration * float(shift.wage_per_hour)
        
        writer.writerow([
            shift.title,
            shift.start_time.strftime('%d/%m/%Y'),
            shift.start_time.strftime('%H:%M'),
            shift.end_time.strftime('%H:%M'),
            app.student.full_name,
            app.student.student_code,
            app.student.class_name,
            shift.wage_per_hour,
            f"{duration:.1f}",
            f"{total_wage:.0f}",
            app.rating_from_employer or 'Chưa đánh giá',
            app.get_status_display()
        ])
        
    return response


@login_required
def employer_workers_view(request):
    """Doanh nghiệp quản lý danh sách sinh viên đã và đang làm việc."""
    user = request.user
    if not hasattr(user, 'employer_profile'):
        return HttpResponseForbidden('Bạn không có quyền truy cập trang này.')
        
    profile = user.employer_profile
    
    # Lấy danh sách ứng viên (đã từng đăng ký các ca của doanh nghiệp này)
    # Gom nhóm theo sinh viên, tính số ca đã nhận, số ca hoàn thành, điểm đánh giá trung bình từ doanh nghiệp
    from django.db.models import Count, Avg, Q
    
    workers = StudentProfile.objects.filter(
        applications__shift__employer=profile
    ).annotate(
        total_shifts=Count('applications', filter=Q(applications__shift__employer=profile)),
        completed_shifts=Count('applications', filter=Q(applications__shift__employer=profile, applications__status='Completed')),
        avg_rating=Avg('applications__rating_from_employer', filter=Q(applications__shift__employer=profile))
    ).distinct()
    
    return render(request, 'core/employer_workers.html', {
        'workers': workers,
        'profile': profile,
    })



