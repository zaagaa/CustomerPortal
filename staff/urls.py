from django.urls import path
from . import views

urlpatterns = [
    path('profile/', views.staff_profile, name='staff_profile'),
path('leave/', views.book_leave, name='book_leave'),
path('leave/summary/', views.get_leave_summary, name='leave_summary'),
path('leave/delete/<uuid:leave_id>/', views.delete_leave, name='delete_leave'),
path('leave/calendar-data/', views.calendar_leave_status, name='calendar_leave_status'),


path("my-attendance/", views.attendance_summary, name="staff_attendance_summary"),




]
