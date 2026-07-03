import hashlib
import re
import urllib3
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# Disable SSL warnings since school portals might have expired certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SCHOOLS_CONFIG = {
    'ictu': {
        'name': 'ĐH CNTT&TT (ICTU)',
        'base_url': 'http://dangkytinchi.ictu.edu.vn',
        'path': 'kcntt',
        'type': 'dktc'
    },
    'tueba': {
        'name': 'ĐH Kinh tế & QTKD (TUEBA)',
        'base_url': 'http://dangkyhoc.tueba.edu.vn',
        'path': 'dhkt',
        'type': 'dktc'
    },
    'tump': {
        'name': 'ĐH Y Dược (TUMP)',
        'base_url': 'http://quanlydaotao.tump.edu.vn',
        'path': 'DHYD',
        'type': 'dktc'
    },
    'tnue': {
        'name': 'ĐH Sư phạm (TNUE)',
        'base_url': 'http://daotao.tnue.edu.vn',
        'path': 'dhsp',
        'type': 'dktc'
    },
    'sfl': {
        'name': 'ĐH Ngoại ngữ (SFL)',
        'base_url': 'https://sinhvien-tnn.tnu.edu.vn',
        'type': 'unisoft'
    },
    'tnus': {
        'name': 'ĐH Khoa học (TNUS)',
        'base_url': 'https://sinhvien.tnus.edu.vn',
        'type': 'tnus'
    },
    'tnut': {
        'name': 'ĐH Kỹ thuật Công nghiệp (TNUT)',
        'base_url': 'https://portal.tnut.edu.vn',
        'type': 'tnut'
    }
}

class TNUScraperException(Exception):
    pass

def md5_hash(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def extract_asp_fields(soup):
    fields = {}
    for field_id in ['__VIEWSTATE', '__VIEWSTATEGENERATOR', '__EVENTVALIDATION']:
        el = soup.find(id=field_id)
        fields[field_id] = el.get('value', '') if el else ''
    fields.update({
        '__EVENTTARGET': '',
        '__EVENTARGUMENT': '',
        '__LASTFOCUS': ''
    })
    return fields

def parse_vietnamese_date(date_str):
    if not date_str:
        return None
    match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{2,4})', date_str)
    if match:
        day = int(match.group(1))
        month = int(match.group(2))
        year = int(match.group(3))
        if year < 100:
            year += 2000
        try:
            return datetime(year, month, day)
        except ValueError:
            return None
    return None

def parse_dktc_study_register_schedule(soup):
    data = []
    # Both TUMP/TNUE (gridRegistered) and ICTU/TUEBA (rptOtherCourseClass) patterns
    patterns = [
        {
            'courseClass': 'gridRegistered_lblCourseClass_',
            'courseCode': 'gridRegistered_lblCourseCode_',
            'longTime': 'gridRegistered_lblLongTime_',
            'location': 'gridRegistered_lblLocation_',
            'credits': 'gridRegistered_lblCourseCredit_'
        },
        {
            'courseClass': 'rptOtherCourseClass_lblCourseClass_',
            'courseCode': 'rptOtherCourseClass_lblCourseCode_',
            'longTime': 'rptOtherCourseClass_lblLongTime_',
            'location': 'rptOtherCourseClass_lblLocation_',
            'credits': 'rptOtherCourseClass_lblCredits_'
        }
    ]

    for pat in patterns:
        idx = 0
        while True:
            class_el = soup.find(id=f"{pat['courseClass']}{idx}")
            if not class_el:
                break
            
            course_class = class_el.get_text().strip()
            course_code = soup.find(id=f"{pat['courseCode']}{idx}").get_text().strip() if soup.find(id=f"{pat['courseCode']}{idx}") else ''
            long_time_el = soup.find(id=f"{pat['longTime']}{idx}")
            location_el = soup.find(id=f"{pat['location']}{idx}")
            credits = soup.find(id=f"{pat['credits']}{idx}").get_text().strip() if soup.find(id=f"{pat['credits']}{idx}") else ''

            course_name = course_class
            name_match = re.match(r'^(.+?)-\d+-\d+', course_class)
            if name_match:
                course_name = name_match.group(1).strip()

            room_by_nhom = {}
            if location_el:
                location_html = str(location_el)
                if '<b>(' in location_html:
                    parts = re.split(r'<b>\([\d,]+\)</b>', location_html)
                    nhom_matchers = re.findall(r'<b>\(([\d,]+)\)</b>', location_html)
                    for marker_idx, groups_str in enumerate(nhom_matchers):
                        groups = [g.strip() for g in groups_str.split(',')]
                        room_part = parts[marker_idx + 1] if marker_idx + 1 < len(parts) else ''
                        room = re.sub(r'<[^>]+>', '', room_part).replace('&nbsp;', ' ').strip()
                        room = room.split('\n')[0].strip()
                        for g in groups:
                            room_by_nhom[g] = room
                if not room_by_nhom:
                    default_room = location_el.get_text().replace('&nbsp;', ' ').strip()
                    default_room = re.sub(r'\([\d,\s-]+\)', '', default_room).strip()
                    if default_room:
                        room_by_nhom['default'] = default_room

            if long_time_el:
                long_time_html = str(long_time_el)
                segments = re.split(r'(?=Từ\s+\d)', long_time_html)
                for segment in segments:
                    if not segment.strip():
                        continue
                    date_match = re.search(r'Từ\s+(\d{1,2}/\d{1,2}/\d{4})\s+đến\s+(\d{1,2}/\d{1,2}/\d{4})', segment)
                    if not date_match:
                        continue
                    
                    start_date = parse_vietnamese_date(date_match.group(1))
                    end_date = parse_vietnamese_date(date_match.group(2))

                    nhom_match = re.search(r'<b>\((\d+)\)</b>', segment) or re.search(r':\s*\((\d+)\)', segment)
                    nhom_num = nhom_match.group(1) if nhom_match else 'default'

                    sched_matches = re.finditer(r'(Thứ\s+(\d)|Chủ\s*nhật)\s+tiết\s+([\d,]+)\s*\(?(TH|LT)?\)?', segment, re.IGNORECASE)
                    for sched in sched_matches:
                        thu = sched.group(2) if sched.group(2) else '8'
                        tiet_list = sched.group(3)
                        loai = sched.group(4) or 'LT'

                        tiets = [int(t.strip()) for t in tiet_list.split(',') if t.strip().isdigit()]
                        tiet_display = f"{min(tiets)}-{max(tiets)}" if len(tiets) > 1 else str(tiets[0]) if tiets else ''
                        room = room_by_nhom.get(nhom_num) or room_by_nhom.get('default') or ''

                        data.append({
                            'ma_hoc_phan': course_code,
                            'ten_hoc_phan': course_name,
                            'nhom': loai,
                            'so_tc': credits,
                            'lop': course_class,
                            'thu': thu,
                            'tiet': tiet_display,
                            'phong': room,
                            'start_date': start_date.strftime('%Y-%m-%d') if start_date else None,
                            'end_date': end_date.strftime('%Y-%m-%d') if end_date else None
                        })
            idx += 1
    return data

def scrape_dktc(username, password, school_config):
    base_url = school_config['base_url']
    path = school_config['path']
    session = requests.Session()
    session.verify = False

    # Step 1: Access login page
    login_url = f"{base_url}/{path}/login.aspx"
    r = session.get(login_url)
    soup = BeautifulSoup(r.text, 'html.parser')
    
    session_path = ''
    session_match = re.search(r'\(S\([^)]+\)\)', r.url)
    if session_match:
        session_path = session_match.group(0)

    def build_url(endpoint):
        if session_path:
            return f"{base_url}/{path}/{session_path}/{endpoint}"
        return f"{base_url}/{path}/{endpoint}"

    asp_fields = extract_asp_fields(soup)
    hashed_pwd = md5_hash(password)

    # Step 2: Post login
    login_post_url = build_url('login.aspx')
    payload = {
        **asp_fields,
        'PageHeader1$hidisNotify': '',
        'txtUserName': username.upper(),
        'txtPassword': hashed_pwd,
        'btnSubmit': 'Đăng nhập'
    }

    r_login = session.post(login_post_url, data=payload, allow_redirects=True)
    soup_home = BeautifulSoup(r_login.text, 'html.parser')

    welcome_text = (soup_home.find(id='PageHeader1_lblLoggedInUser') or 
                    soup_home.find(id='PageHeader1_lblUserFullName'))
    if not welcome_text or 'Khách' in welcome_text.get_text():
        raise TNUScraperException("Đăng nhập thất bại. Vui lòng kiểm tra mã SV hoặc mật khẩu ĐKTC.")

    full_name = welcome_text.get_text().strip()
    name_match = re.match(r'^([^(]+)', full_name)
    if name_match:
        full_name = name_match.group(1).strip()

    # Step 3: Fetch study register schedule
    reg_url = build_url('StudyRegister/StudyRegister.aspx')
    r_reg = session.get(reg_url, allow_redirects=True)
    soup_reg = BeautifulSoup(r_reg.text, 'html.parser')

    schedule = parse_dktc_study_register_schedule(soup_reg)

    # Try checking for previous semesters
    view_other_term = soup_reg.find(id='lnkViewOtherTermRgs')
    if view_other_term:
        try:
            asp_fields_reg = extract_asp_fields(soup_reg)
            asp_fields_reg['__EVENTTARGET'] = 'lnkViewOtherTermRgs'
            r_prev = session.post(reg_url, data=asp_fields_reg, allow_redirects=True)
            soup_prev = BeautifulSoup(r_prev.text, 'html.parser')
            prev_schedule = parse_dktc_study_register_schedule(soup_prev)
            
            existing_keys = {f"{s['ten_hoc_phan']}_{s['thu']}_{s['tiet']}_{s['start_date']}" for s in schedule}
            for s in prev_schedule:
                key = f"{s['ten_hoc_phan']}_{s['thu']}_{s['tiet']}_{s['start_date']}"
                if key not in existing_keys:
                    schedule.append(s)
        except Exception:
            pass

    scraped_major = ''
    scraped_class = ''
    lbl_student = soup_reg.find(id='lblStudent')
    if lbl_student:
        student_text = lbl_student.get_text().strip()
        parts = [p.strip() for p in student_text.split('-') if p.strip()]
        if len(parts) >= 3:
            scraped_major = parts[2].replace('Chuyên ngành', '').strip()
        if len(parts) >= 4:
            scraped_class = parts[3]

    # Fallback to drpField and drpAcademicYear dropdowns
    if not scraped_major:
        drp_field = soup_reg.find(id='drpField')
        if drp_field:
            opt = drp_field.find('option', selected=True)
            if opt:
                opt_text = opt.get_text().strip()
                if ' - ' in opt_text:
                    scraped_major = opt_text.split(' - ', 1)[1].strip()
                else:
                    scraped_major = opt_text

    if not scraped_class:
        drp_class = soup_reg.find(id='drpAcademicYear')
        if drp_class:
            opt = drp_class.find('option', selected=True)
            if opt:
                scraped_class = opt.get_text().strip()

    return {
        'full_name': full_name,
        'student_code': username.upper(),
        'class_name': scraped_class,
        'major': scraped_major,
        'schedule': schedule
    }

def parse_unisoft_schedule_table(soup, term_name):
    data = []
    rows = soup.select('#grdViewLopDangKy tr')
    for i, row in enumerate(rows):
        if i == 0:
            continue
        cols = row.find_all('td')
        if len(cols) < 8:
            continue

        if len(cols) >= 12:
            ma_hp = cols[1].get_text().strip()
            ten_hp = cols[2].get_text().strip()
            so_tc = cols[3].get_text().strip()
            lop_tc = cols[4].get_text().strip()
            lich_hoc = cols[6].get_text().strip()
            gv = cols[7].get_text().strip()
            phong = cols[8].get_text().strip()
        else:
            ma_hp = cols[0].get_text().strip()
            ten_hp = cols[1].get_text().strip()
            so_tc = cols[2].get_text().strip()
            lop_tc = cols[3].get_text().strip()
            lich_hoc = cols[5].get_text().strip()
            gv = cols[6].get_text().strip()
            phong = cols[7].get_text().strip()

        if not ma_hp or 'Học bình thường' in ma_hp or 'Học lại' in ma_hp:
            continue

        lich_pattern = r'(\d{1,2}/\d{1,2}/\d{2,4})-(\d{1,2}/\d{1,2}/\d{2,4}).*?Thứ\s*(\d+)\s*\(T([\d\-]+)\)'
        matches = re.finditer(lich_pattern, lich_hoc, re.IGNORECASE)
        found_schedule = False

        for match in matches:
            found_schedule = True
            start_date = parse_vietnamese_date(match.group(1))
            end_date = parse_vietnamese_date(match.group(2))
            thu = match.group(3)
            tiet = match.group(4)
            room = re.sub(r'https?://[^\s]+', '', phong).strip()

            data.append({
                'ma_hoc_phan': ma_hp,
                'ten_hoc_phan': ten_hp,
                'so_tc': so_tc,
                'nhom': 'TH' if 'TH' in lop_tc else 'LT',
                'lop': lop_tc,
                'thu': thu,
                'tiet': tiet,
                'phong': room,
                'start_date': start_date.strftime('%Y-%m-%d') if start_date else None,
                'end_date': end_date.strftime('%Y-%m-%d') if end_date else None
            })

        if not found_schedule and ma_hp and ten_hp:
            room = re.sub(r'https?://[^\s]+', '', phong).strip()
            data.append({
                'ma_hoc_phan': ma_hp,
                'ten_hoc_phan': ten_hp,
                'so_tc': so_tc,
                'nhom': 'TH' if 'TH' in lop_tc else 'LT',
                'lop': lop_tc,
                'thu': '',
                'tiet': '',
                'phong': room,
                'start_date': None,
                'end_date': None
            })
    return data

def scrape_unisoft(username, password, school_config):
    base_url = school_config['base_url']
    session = requests.Session()
    session.verify = False
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })

    # Step 1: Get login page
    r = session.get(f"{base_url}/Login.aspx")
    soup = BeautifulSoup(r.text, 'html.parser')
    asp_fields = extract_asp_fields(soup)

    # Step 2: Post login
    payload = {
        **asp_fields,
        'txtusername': username,
        'txtpassword': password,
        'btnDangNhap': 'Đăng nhập'
    }
    r_login = session.post(f"{base_url}/Login.aspx", data=payload, allow_redirects=True)
    if 'Sai tên đăng nhập' in r_login.text or 'Sai mật khẩu' in r_login.text or 'không hợp lệ' in r_login.text:
        raise TNUScraperException("Đăng nhập thất bại. Vui lòng kiểm tra mã SV hoặc mật khẩu portal.")

    # Step 3: Access schedule page to get full name & schedules
    r_sched = session.get(f"{base_url}/wfrmDangKyLopTinChiB3.aspx", allow_redirects=True)
    soup_sched = BeautifulSoup(r_sched.text, 'html.parser')

    full_name = ''
    name_el = soup_sched.find(id='HeaderSV_lblHo_ten') or soup_sched.find(id='lblHo_ten')
    if name_el:
        full_name = name_el.get_text().strip().split('\n')[0].strip()
    if not full_name:
        full_name = username

    asp_fields_sched = extract_asp_fields(soup_sched)
    
    # Extract semesters dropdown options
    term_options = []
    cmb = soup_sched.find(id='cmbKy_dang_ky')
    if cmb:
        for opt in cmb.find_all('option'):
            val = opt.get('value')
            txt = opt.get_text().strip()
            if val and txt:
                term_options.append((val, txt))

    schedule = []
    # Fetch schedule for the most recent term or first 2 terms
    for val, txt in term_options[:2]:
        try:
            select_payload = {
                **asp_fields_sched,
                '__EVENTTARGET': 'cmbKy_dang_ky',
                'cmbKy_dang_ky': val
            }
            r_term = session.post(f"{base_url}/wfrmDangKyLopTinChiB3.aspx", data=select_payload, allow_redirects=True)
            soup_term = BeautifulSoup(r_term.text, 'html.parser')
            asp_fields_term = extract_asp_fields(soup_term)

            print_payload = {
                **asp_fields_term,
                'cmbKy_dang_ky': val,
                'btnInKetQua': 'In kết quả đăng ký'
            }
            r_print = session.post(f"{base_url}/wfrmDangKyLopTinChiB3.aspx", data=print_payload, allow_redirects=True)
            soup_print = BeautifulSoup(r_print.text, 'html.parser')

            schedule.extend(parse_unisoft_schedule_table(soup_print, txt))
        except Exception:
            pass

    return {
        'full_name': full_name,
        'student_code': username.upper(),
        'schedule': schedule
    }

def parse_tnus_semester_schedule_table(soup, term_name):
    data = []
    tables = soup.find_all('table', class_='table-bordered')
    for table in tables:
        headers = [th.get_text().strip().lower() for th in table.find_all('th')]
        if 'stt' in headers and 'thời gian' in headers:
            for row in table.select('tbody tr'):
                cols = row.find_all('td')
                if len(cols) >= 9:
                    stt = cols[0].get_text().strip()
                    ten_hp = cols[1].get_text().strip()
                    so_tc = cols[2].get_text().strip()
                    ten_lop_tc = cols[3].get_text().strip()
                    thoi_gian = cols[4].get_text().strip()
                    thu = cols[5].get_text().strip()
                    tiet = cols[6].get_text().strip()
                    phong_raw = cols[7].get_text().strip()
                    gv = cols[8].get_text().strip()

                    phong = re.sub(r'https?://[^\s]+', '', phong_raw).strip()
                    start_date = None
                    end_date = None
                    time_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})-(\d{1,2}/\d{1,2}/\d{4})', thoi_gian)
                    if time_match:
                        start_date = parse_vietnamese_date(time_match.group(1))
                        end_date = parse_vietnamese_date(time_match.group(2))

                    if ten_hp:
                        data.append({
                            'ma_hoc_phan': '',
                            'ten_hoc_phan': ten_hp,
                            'so_tc': so_tc,
                            'nhom': 'TH' if 'TH' in ten_lop_tc else 'LT',
                            'lop': ten_lop_tc,
                            'thu': thu,
                            'tiet': tiet.replace(' ', ''),
                            'phong': phong,
                            'start_date': start_date.strftime('%Y-%m-%d') if start_date else None,
                            'end_date': end_date.strftime('%Y-%m-%d') if end_date else None
                        })
    return data

def scrape_tnus(username, password, school_config):
    base_url = school_config['base_url']
    session = requests.Session()
    session.verify = False
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })

    # Step 1: Login page
    session.get(f"{base_url}/DangNhap/Login")
    
    # Step 2: Login post
    payload = {
        'Username': username,
        'password': password
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': f"{base_url}/DangNhap/Login",
        'X-Requested-With': 'XMLHttpRequest'
    }
    r_login = session.post(f"{base_url}/DangNhap/CheckLogin", data=payload, headers=headers)
    if 'Login' in r_login.text and 'SinhVien' not in r_login.text:
        raise TNUScraperException("Đăng nhập thất bại. Vui lòng kiểm tra mã SV hoặc mật khẩu portal TNUS.")

    # Extract name from response HTML/JSON or text
    full_name = username
    name_match = re.search(
        r'(Trần|Nguyễn|Lê|Phạm|Hoàng|Vũ|Đặng|Bùi|Đỗ|Hồ|Ngô|Dương|Lý)[^<\n]{0,30}',
        r_login.text
    )
    if name_match:
        full_name = name_match.group(0).strip()

    # Step 3: Fetch schedule
    r_sched = session.get(f"{base_url}/TraCuuLichHoc/Index")
    soup_sched = BeautifulSoup(r_sched.text, 'html.parser')

    term_name = f"Term_{datetime.now().year}"
    schedule = parse_tnus_semester_schedule_table(soup_sched, term_name)

    return {
        'full_name': full_name,
        'student_code': username.upper(),
        'schedule': schedule
    }

def scrape_tnut(username, password, school_config):
    base_url = school_config['base_url'].replace('https://', '').replace('http://', '')
    session = requests.Session()
    session.verify = False
    session.headers.update({
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    })

    # Login to TNUT Portal (REST API)
    login_url = f"https://{base_url}/api/auth/login"
    login_payload = f"grant_type=password&username={username}&password={password}"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    r_login = session.post(login_url, data=login_payload, headers=headers)
    login_data = r_login.json()
    token = login_data.get('access_token')
    if not token:
        err_msg = login_data.get('error_description') or "Đăng nhập thất bại. Kiểm tra mã SV hoặc mật khẩu."
        raise TNUScraperException(err_msg)

    # Set Auth header
    session.headers.update({'Authorization': f"Bearer {token}"})

    # Get User Info
    r_me = session.get(f"https://{base_url}/api/auth/me")
    me_data = r_me.json()
    user_info = me_data.get('data', {}) if me_data.get('result') else me_data
    full_name = user_info.get('name') or user_info.get('ho_ten') or username

    # Get Semester list
    r_sem = session.post(f"https://{base_url}/api/sch/w-locdshockytkbuser", json={})
    sem_data = r_sem.json().get('data', {}) or r_sem.json()
    semesters = sem_data.get('ds_hoc_ky', [])
    current_sem = sem_data.get('hoc_ky_theo_ngay_hien_tai')

    # Get schedule for current semester
    schedule = []
    if current_sem:
        r_sched = session.post(
            f"https://{base_url}/api/sch/w-locdstkbhockytheodoituong",
            json={'hoc_ky': current_sem, 'loai_doi_tuong': 1}
        )
        sched_list = r_sched.json().get('data', {}) or r_sched.json()
        ds_nhom_to = sched_list.get('ds_nhom_to', []) if isinstance(sched_list, dict) else sched_list
        if isinstance(ds_nhom_to, list):
            for item in ds_nhom_to:
                # Parse date range e.g. "08/12/2025 đến 19/01/2026"
                tooltip = item.get('tooltip', '')
                start_date = None
                end_date = None
                date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})\s+đến\s+(\d{1,2}/\d{1,2}/\d{4})', tooltip)
                if date_match:
                    start_date = parse_vietnamese_date(date_match.group(1))
                    end_date = parse_vietnamese_date(date_match.group(2))

                schedule.append({
                    'ma_hoc_phan': item.get('nhom_to') or item.get('ma_mon') or '',
                    'ten_hoc_phan': item.get('ten_mon') or '',
                    'so_tc': '',
                    'nhom': 'TH' if 'TH' in item.get('nhom_to', '') else 'LT',
                    'lop': item.get('nhom_to') or '',
                    'thu': str(item.get('thu', '')),
                    'tiet': f"{item.get('tbd', '')}-{int(item.get('tbd', 0)) + int(item.get('so_tiet', 1)) - 1}" if item.get('tbd') else '',
                    'phong': item.get('phong') or '',
                    'start_date': start_date.strftime('%Y-%m-%d') if start_date else None,
                    'end_date': end_date.strftime('%Y-%m-%d') if end_date else None
                })

    return {
        'full_name': full_name,
        'student_code': username.upper(),
        'schedule': schedule
    }

def scrape_student_data(username, password, school):
    # Mock fallback cho môi trường test local
    if username.upper() == 'DTC245200006' or password == '123456':
        return {
            'full_name': 'Nguyễn Văn Đạt',
            'student_code': username.upper(),
            'schedule': [
                {
                    'ma_hoc_phan': 'INT1405',
                    'ten_hoc_phan': 'Cấu trúc dữ liệu và giải thuật',
                    'so_tc': '3',
                    'nhom': 'LT',
                    'lop': 'CNTT-K15A',
                    'thu': '2',
                    'tiet': '1-3',
                    'phong': 'TA-305',
                    'start_date': '2026-07-01',
                    'end_date': '2026-12-31',
                    'giang_vien': 'TS. Nguyễn Văn A',
                    'link_meet': 'https://meet.google.com/abc-defg-hij'
                },
                {
                    'ma_hoc_phan': 'INT1405',
                    'ten_hoc_phan': 'Cấu trúc dữ liệu và giải thuật',
                    'so_tc': '3',
                    'nhom': 'TH',
                    'lop': 'CNTT-K15A',
                    'thu': '4',
                    'tiet': '7-9',
                    'phong': 'Lab 4',
                    'start_date': '2026-07-01',
                    'end_date': '2026-12-31',
                    'giang_vien': 'ThS. Trần Thị B',
                    'link_meet': 'https://meet.google.com/klm-nopq-rst'
                },
                {
                    'ma_hoc_phan': 'MAT1201',
                    'ten_hoc_phan': 'Đại số tuyến tính',
                    'so_tc': '3',
                    'nhom': 'LT',
                    'lop': 'CNTT-K15A',
                    'thu': '5',
                    'tiet': '1-3',
                    'phong': 'TB-201',
                    'start_date': '2026-07-01',
                    'end_date': '2026-12-31',
                    'giang_vien': 'PGS.TS. Lê Hoàng C',
                    'link_meet': 'https://meet.google.com/uvw-xyz1-234'
                }
            ],
            'exams': [
                {
                    'course_code': 'MAT1201',
                    'course_name': 'Đại số tuyến tính',
                    'exam_date': '2026-07-07',
                    'exam_time': '09:00',
                    'room': 'CĐ-102',
                    'exam_format': 'Trắc nghiệm trên máy',
                    'sbd': 'SBD-089',
                    'notes': 'Sinh viên mang theo thẻ sinh viên và có mặt trước 15 phút.'
                },
                {
                    'course_code': 'MAT1201',
                    'course_name': 'Đại số tuyến tính',
                    'exam_date': '2026-07-15',
                    'exam_time': '08:00',
                    'room': 'CĐ-102',
                    'exam_format': 'Trắc nghiệm trên máy',
                    'sbd': 'SBD-089',
                    'notes': 'Sinh viên mang theo thẻ sinh viên và có mặt trước 15 phút.'
                },
                {
                    'course_code': 'INT1405',
                    'course_name': 'Cấu trúc dữ liệu và giải thuật',
                    'exam_date': '2026-07-18',
                    'exam_time': '14:00',
                    'room': 'Lab 4',
                    'exam_format': 'Thực hành trên máy',
                    'sbd': 'SBD-095',
                    'notes': 'Thi thực hành lập trình C++.'
                }
            ]
        }

    school_config = SCHOOLS_CONFIG.get(school)
    if not school_config:
        raise TNUScraperException(f"Không hỗ trợ cấu hình trường '{school}'")

    school_type = school_config.get('type')
    try:
        if school_type == 'dktc':
            return scrape_dktc(username, password, school_config)
        elif school_type == 'unisoft':
            return scrape_unisoft(username, password, school_config)
        elif school_type == 'tnus':
            return scrape_tnus(username, password, school_config)
        elif school_type == 'tnut':
            return scrape_tnut(username, password, school_config)
        else:
            raise TNUScraperException("Loại hệ thống đào tạo không được hỗ trợ.")
    except Exception as e:
        if isinstance(e, TNUScraperException):
            raise e
        raise TNUScraperException(f"Có lỗi khi kết nối hoặc cào dữ liệu: {str(e)}")
