"""
URL configuration cho app Core.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Trang chủ
    path('', views.home_view, name='home'),

    # Hồ sơ
    path('profile/complete/', views.complete_profile_view, name='complete_profile'),
    path('student/profile/', views.student_profile_view, name='student_profile'),
    path('student/settings/', views.student_settings_view, name='student_settings'),
    path('employer/register/', views.register_employer_view, name='register_employer'),

    # Dashboard
    path('student/dashboard/', views.student_dashboard_view, name='student_dashboard'),
    path('student/schedule/refresh/', views.refresh_schedule_view, name='refresh_schedule'),
    path('student/find-shifts/', views.find_shifts_view, name='find_shifts'),
    path('student/ajax/find-shifts/', views.ajax_find_shifts_view, name='ajax_find_shifts'),
    path('student/exams/', views.exam_schedule_view, name='exam_schedule'),
    path('employer/dashboard/', views.employer_dashboard_view, name='employer_dashboard'),
    path('employer/workers/', views.employer_workers_view, name='employer_workers'),
    path('employer/export-csv/', views.employer_export_csv_view, name='employer_export_csv'),
    path('employer/student/<int:student_id>/profile/', views.employer_student_profile_view, name='employer_student_profile'),
    path('employer/shift/<int:shift_id>/edit/', views.edit_shift_view, name='edit_shift'),
    path('employer/application/<int:application_id>/cancel/', views.employer_cancel_application_view, name='employer_cancel_application'),

    # Ca làm việc
    path('shift/create/', views.create_shift_view, name='create_shift'),
    path('shift/<int:shift_id>/', views.shift_detail_view, name='shift_detail'),
    path('shift/<int:shift_id>/delete/', views.delete_shift_view, name='delete_shift'),
    path('shift/<int:shift_id>/apply/', views.apply_shift_view, name='apply_shift'),

    # Check-in / Check-out
    path('application/<int:application_id>/checkin/', views.check_in_view, name='check_in'),
    path('application/<int:application_id>/checkout/', views.check_out_view, name='check_out'),

    # Đánh giá
    path('application/<int:application_id>/rate/', views.rate_view, name='rate'),

    # Khung giờ rảnh
    path('timeblock/add/', views.add_time_block_view, name='add_time_block'),
    path('timeblock/<int:block_id>/delete/', views.delete_time_block_view, name='delete_time_block'),

    # Quản trị hệ thống
    path('portal-admin/overview/', views.admin_dashboard_view, name='admin_dashboard'),
    path('portal-admin/shift/create/', views.admin_create_shift_view, name='admin_create_shift'),
    path('portal-admin/shift/<int:shift_id>/edit/', views.admin_edit_shift_view, name='admin_edit_shift'),
    path('portal-admin/shift/<int:shift_id>/delete/', views.admin_delete_shift_view, name='admin_delete_shift'),
    path('portal-admin/employer/<int:employer_id>/verify/', views.verify_employer_view, name='verify_employer'),
    path('portal-admin/manual-match/', views.manual_match_view, name='manual_match'),
    path('portal-admin/student/create/', views.admin_create_student_view, name='admin_create_student'),
    path('portal-admin/student/<int:student_id>/edit/', views.admin_edit_student_view, name='admin_edit_student'),
    path('portal-admin/student/<int:student_id>/delete/', views.admin_delete_student_view, name='admin_delete_student'),
    path('portal-admin/employer/create/', views.admin_create_employer_view, name='admin_create_employer'),
    path('portal-admin/employer/<int:employer_id>/edit/', views.admin_edit_employer_view, name='admin_edit_employer'),
    path('portal-admin/employer/<int:employer_id>/delete/', views.admin_delete_employer_view, name='admin_delete_employer'),
    path('portal-admin/application/<int:application_id>/delete/', views.admin_delete_application_view, name='admin_delete_application'),
]
