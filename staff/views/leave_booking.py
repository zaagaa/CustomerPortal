

from django.shortcuts import render, redirect, get_object_or_404

from django.http import JsonResponse
from django.contrib import messages
from datetime import date
import uuid

from dashboard.models import Setting
from staff.forms import StaffLeaveForm
from staff.models import StaffLeave
from staff.utils import get_staff_by_mobile, get_staff_name_by_id
from calendar import monthrange
from django.utils.dateparse import parse_date

from django.utils import timezone





# Constants
MAX_MONTHLY_LEAVE_PER_USER = float(Setting.objects.filter(setting='monthly_leave_per_staff').values_list('value', flat=True).first() or 0)
MAX_DAILY_LEAVE = float(Setting.objects.filter(setting='daily_leave_all_staff').values_list('value', flat=True).first() or 0)
FULL_LEAVE = 1
HALF_LEAVE = 0.5

unit_map = {
    'FULL': FULL_LEAVE,
    'HALF_MORNING': HALF_LEAVE,
    'HALF_AFTERNOON': HALF_LEAVE,
}


def calendar_leave_status(request):
    month_str = request.GET.get('month') or timezone.now().strftime('%Y-%m')
    year, month = map(int, month_str.split('-'))
    start_date = date(year, month, 1)
    end_date = date(year, month, monthrange(year, month)[1])

    leaves = StaffLeave.objects.filter(leave_date__range=(start_date, end_date), status='APPROVED')

    status_by_date = {}

    for day in range(1, end_date.day + 1):
        current_date = date(year, month, day)
        day_leaves = leaves.filter(leave_date=current_date)

        total_units = 0.0
        for leave in day_leaves:
            total_units += unit_map.get(leave.leave_type, 0)

        status = "full" if total_units >= MAX_DAILY_LEAVE else "available"
        status_by_date[day] = {"status": status}

    return JsonResponse({'year': year, 'month': month, 'days': status_by_date})

def delete_leave(request, leave_id):
    mobile = request.session.get('customer_mobile') or request.COOKIES.get('customer_mobile')
    staff = get_staff_by_mobile(mobile)
    if not staff:
        messages.error(request, "Unauthorized.")
        return redirect('home')

    leave = get_object_or_404(StaffLeave, id=leave_id)
    if str(leave.staff_id) != str(staff['id']):
        messages.error(request, "You are not allowed to delete this leave.")
        return redirect('book_leave')

    if leave.leave_date <= date.today():
        messages.warning(request, "Cannot delete leave for today or past.")
        return redirect('book_leave')

    leave.delete()
    messages.success(request, "Leave booking deleted.")

    same_day_leaves = StaffLeave.objects.filter(leave_date=leave.leave_date).order_by('created_at')
    approved_count = sum(unit_map.get(l.leave_type, 0) for l in same_day_leaves.filter(status='APPROVED'))
    if approved_count < MAX_DAILY_LEAVE:
        waiting = same_day_leaves.filter(status='WAITING').first()
        if waiting:
            waiting.status = 'APPROVED'
            waiting.save()

    return redirect('book_leave')


def get_leave_summary(request):
    date_str = request.GET.get('date')
    if not date_str:
        return JsonResponse({'success': False, 'message': 'No date provided'})

    date_obj = parse_date(date_str)
    leaves = StaffLeave.objects.filter(leave_date=date_obj, status='APPROVED')

    slot_count = {
        'FULL': 0,
        'HALF_MORNING': 0,
        'HALF_AFTERNOON': 0,
    }

    total_units = 0.0
    for leave in leaves:
        lt = leave.leave_type
        if lt == 'FULL':
            slot_count[lt] += FULL_LEAVE
        else:
            slot_count[lt] += HALF_LEAVE


        total_units += unit_map.get(lt, 0)

    available_units = MAX_DAILY_LEAVE - total_units
    slots = []

    if available_units >= MAX_DAILY_LEAVE:
        if slot_count['FULL'] < (MAX_DAILY_LEAVE):
            slots.append("Full Day")
    if available_units >= HALF_LEAVE:
        if slot_count['HALF_MORNING'] < (MAX_DAILY_LEAVE * HALF_LEAVE):
            slots.append("Half Morning")
        if slot_count['HALF_AFTERNOON'] < (MAX_DAILY_LEAVE * HALF_LEAVE):
            slots.append("Half Afternoon")

    readable = " + ".join(slots) if slots else "No slots available"

    booked = [
        {
            "name": get_staff_name_by_id(leave.staff_id),
            "status": leave.status,
            "type": leave.leave_type.replace('_', ' ').title()
        }
        for leave in leaves
    ]

    return JsonResponse({
        'success': True,
        'booked': booked,
        'available_slots': readable,
    })
from django.urls import reverse
from django.utils.http import urlencode

def book_leave(request):
    mobile = request.session.get('customer_mobile') or request.COOKIES.get('customer_mobile')
    staff = get_staff_by_mobile(mobile)
    if not staff:
        return redirect('home')

    staff_id = staff['id']
    today = timezone.localdate()

    if request.method == 'POST':
        form = StaffLeaveForm(request.POST)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.id = uuid.uuid4()
            leave.staff_id = staff_id
            leave.created_at = timezone.now()

            if leave.leave_date < today:
                messages.error(request, "Cannot book leave for past dates.")
                return redirect(f"{reverse('book_leave')}?{urlencode({'date': leave.leave_date})}")

            if StaffLeave.objects.filter(staff_id=staff_id, leave_date=leave.leave_date).exists():
                messages.warning(request, "You have already booked leave for this date.")
                return redirect(f"{reverse('book_leave')}?{urlencode({'date': leave.leave_date})}")

            # Check 1: Future date limit
            max_booking_date = today + timezone.timedelta(days=60)
            if leave.leave_date > max_booking_date:
                messages.warning(request, "You can only book up to 60 days in advance.")
                return redirect(f"{reverse('book_leave')}?{urlencode({'date': leave.leave_date})}")

            # Check 2: Limit approved future leaves
            future_approved_count = StaffLeave.objects.filter(
                staff_id=staff_id,
                leave_date__gt=today,
                status='APPROVED'
            ).count()

            if future_approved_count >= 4:
                messages.warning(request, "You can only have 4 approved future leaves at a time.")
                return redirect(f"{reverse('book_leave')}?{urlencode({'date': leave.leave_date})}")

            # Monthly limit check
            month_start = leave.leave_date.replace(day=1)
            month_end = leave.leave_date.replace(day=monthrange(leave.leave_date.year, leave.leave_date.month)[1])

            approved_leaves = StaffLeave.objects.filter(
                staff_id=staff_id,
                leave_date__range=(month_start, month_end),
                status='APPROVED'
            )
            monthly_used_units = sum(unit_map.get(l.leave_type, 0) for l in approved_leaves)
            current_unit = unit_map.get(leave.leave_type, 0)

            if monthly_used_units + current_unit > MAX_MONTHLY_LEAVE_PER_USER:
                messages.warning(request, f"Monthly limit reached ({monthly_used_units:.1f} used).")
                return redirect(f"{reverse('book_leave')}?{urlencode({'date': leave.leave_date})}")

            # Daily slot validation using your logic
            leaves = StaffLeave.objects.filter(leave_date=leave.leave_date, status='APPROVED')
            slot_count = {
                'FULL': 0,
                'HALF_MORNING': 0,
                'HALF_AFTERNOON': 0,
            }
            total_units = 0.0
            for l in leaves:
                lt = l.leave_type
                if lt == 'FULL':
                    slot_count[lt] += FULL_LEAVE
                else:
                    slot_count[lt] += HALF_LEAVE
                total_units += unit_map.get(lt, 0)

            available_units = MAX_DAILY_LEAVE - total_units

            # Check if the requested slot is available
            slot_allowed = False
            if leave.leave_type == 'FULL':
                if available_units >= MAX_DAILY_LEAVE and slot_count['FULL'] < MAX_DAILY_LEAVE:
                    slot_allowed = True
            elif leave.leave_type == 'HALF_MORNING':
                if available_units >= HALF_LEAVE and slot_count['HALF_MORNING'] < (MAX_DAILY_LEAVE * HALF_LEAVE):
                    slot_allowed = True
            elif leave.leave_type == 'HALF_AFTERNOON':
                if available_units >= HALF_LEAVE and slot_count['HALF_AFTERNOON'] < (MAX_DAILY_LEAVE * HALF_LEAVE):
                    slot_allowed = True

            if not slot_allowed:
                messages.warning(request, f"{leave.leave_type.replace('_', ' ').title()} slot not available.")
                return redirect(f"{reverse('book_leave')}?{urlencode({'date': leave.leave_date})}")

            # Save leave
            leave.status = 'APPROVED'
            leave.save()
            messages.success(request, f"Leave booked ({leave.leave_type.replace('_', ' ').title()})")
            return redirect(f"{reverse('book_leave')}?{urlencode({'date': leave.leave_date})}")

    else:
        form = StaffLeaveForm()

    now = timezone.localdate()
    month_start = now.replace(day=1)
    month_end = now.replace(day=monthrange(now.year, now.month)[1])
    approved_leaves = StaffLeave.objects.filter(
        staff_id=staff_id,
        leave_date__range=(month_start, month_end),
        status='APPROVED'
    )
    monthly_used_units = sum(unit_map.get(l.leave_type, 0) for l in approved_leaves)
    monthly_remaining_units = MAX_MONTHLY_LEAVE_PER_USER - monthly_used_units

    history = StaffLeave.objects.filter(staff_id=staff_id).order_by('-leave_date')

    selected_date_str = request.GET.get('date')
    selected_date = parse_date(selected_date_str) if selected_date_str else None

    return render(request, 'leave_booking.html', {
        'form': form,
        'history': history,
        'staff': staff,
        'today': today,
        'monthly_remaining_units': monthly_remaining_units,
        'max_monthly_units': MAX_MONTHLY_LEAVE_PER_USER,
        'selected_date': selected_date,
    })
