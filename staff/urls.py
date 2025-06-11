from django.urls import path

from staff.views.attendance_summary import attendance_summary
from staff.views.leave_booking import book_leave, get_leave_summary, delete_leave, calendar_leave_status
from staff.views.profile import staff_profile

urlpatterns = [
    path('profile/', staff_profile, name='staff_profile'),
path('leave/', book_leave, name='book_leave'),
path('leave/summary/', get_leave_summary, name='leave_summary'),
path('leave/delete/<uuid:leave_id>/', delete_leave, name='delete_leave'),
path('leave/calendar-data/', calendar_leave_status, name='calendar_leave_status'),


path("my-attendance/", attendance_summary, name="staff_attendance_summary"),




]
