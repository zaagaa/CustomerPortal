from types import SimpleNamespace

from django.shortcuts import render, redirect, get_object_or_404

from django.http import JsonResponse
from django.contrib import messages
from datetime import date
import uuid
from django.db.models import Q, Sum
from .forms import StaffLeaveForm
from .models import StaffLeave, Attendance_Entry
from staff.utils import get_staff_by_mobile, get_staff_name_by_id
from calendar import monthrange
from django.utils.dateparse import parse_date
from datetime import datetime, timezone as dt_timezone  # rename to avoid conflict
from django.utils import timezone
import pytz

IST = pytz.timezone("Asia/Kolkata")

def get_ist_time_from_unix(ts):
    """Convert Unix timestamp to Asia/Kolkata localized time (safe for Django 5.2)"""
    utc_dt = datetime.fromtimestamp(ts, tz=dt_timezone.utc)  # ✅ use renamed dt_timezone
    return utc_dt.astimezone(IST)

# Constants
MAX_MONTHLY_UNITS_PER_USER = 4.0
MAX_DAILY_UNITS = 1
FULL_UNITS = 1
HALF_UNITS = 0.5


from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from datetime import date, datetime, time
from .models import Staff, Staff_Credit
import calendar

def staff_salary(staff_id, month=None):
    today = date.today()
    try:
        dt = datetime.strptime(month, "%Y%m") if month else timezone.now()
    except ValueError:
        dt = timezone.now()



    try:
        staff = Staff.objects.get(id=staff_id)
    except Staff.DoesNotExist:
        return None

    total_salary = staff.salary or 0
    effective_days = max(calendar.monthrange(dt.year, dt.month)[1] - 4, 1)
    full_day_salary = total_salary / effective_days

    start_date = dt.replace(day=1).date()
    end_date = dt.replace(day=calendar.monthrange(dt.year, dt.month)[1]).date()
    loop_end_day = min(end_date.day, today.day if dt.year == today.year and dt.month == today.month else end_date.day)

    print(staff)
    attendance_qs = Attendance_Entry.objects.filter(
        staff=staff,
        date__range=[start_date, end_date]
    )
    attendance_map = {a.date: a for a in attendance_qs}

    total_working_days = 0
    for day in range(1, loop_end_day + 1):
        current_date = dt.replace(day=day).date()
        entry = attendance_map.get(current_date)

        if entry and entry.in_time and entry.out_time:
            in_time_obj = datetime.fromtimestamp(entry.in_time).time()
            out_time_obj = datetime.fromtimestamp(entry.out_time).time()
            late = in_time_obj > time(10, 0)
            early = out_time_obj < time(20, 0)
            total_working_days += 0.5 if (late or early) else 1
        elif entry:
            # total_working_days += 0.5
            pass

    gross_salary = round(total_working_days * full_day_salary, 2)
    credit_total = Staff_Credit.objects.filter(staff=staff, date__range=[start_date, end_date]).aggregate(total=Sum("amount"))["total"] or 0
    net_salary = round(gross_salary - float(credit_total), 2)

    return {
        "gross_salary": gross_salary,
        "credit_total": credit_total,
        "net_salary": net_salary,
        "working_days": total_working_days,
        "monthly_salary": total_salary,
        "dt": dt,
        "full_day_salary": full_day_salary,
        "attendance_map": attendance_map,
        "start_date": start_date,
        "end_date": end_date,
        "loop_end_day": loop_end_day,
        "staff": staff,
    }

def attendance_summary(request):
    company_id = request.COOKIES.get("company_id")
    mobile = request.session.get('customer_mobile') or request.COOKIES.get('customer_mobile')
    # staff = get_staff_by_mobile(mobile)
    staff = Staff.objects.get(mobile=mobile, discontinued=0)
    # staff_list = Staff.objects.filter(company_id=company_id, discontinued=0)
    print(staff.id,"staff.id")

    staff_id = staff.id
    month_str = request.GET.get("month") or timezone.now().strftime("%Y-%m")

    try:
        dt = datetime.strptime(month_str, "%Y-%m")
    except ValueError:
        dt = timezone.now()

    today = date.today()

    context = {
        "month_input": dt.strftime("%Y-%m"),
        "records": [],
        "gross_salary": 0,
        "credit_total": 0,
        "net_salary": 0,
        "salary_value": 0,
        "working_days": 0,
        "credits": [],
        "today": today.isoformat(),
    }

    if not staff_id:
        return render(request, "attendance_summary.html", context)

    data = staff_salary(staff.id, dt.strftime("%Y%m"))
    if not data:
        return render(request, "attendance_summary.html", context)

    daily_records = []
    for day in range(1, data["loop_end_day"] + 1):
        current_date = data["dt"].replace(day=day).date()
        entry = data["attendance_map"].get(current_date)

        record = {
            "date": current_date,
            "in_time": None,
            "out_time": None,
            "status": "ABSENT",
            "amount": 0,
        }

        if entry and entry.in_time and entry.out_time:
            in_time_obj = get_ist_time_from_unix(entry.in_time)
            out_time_obj = get_ist_time_from_unix(entry.out_time)

            record["in_time"] = in_time_obj.strftime("%I:%M:%S %p")
            record["out_time"] = out_time_obj.strftime("%I:%M:%S %p")

            late = in_time_obj.time() > time(10, 0)
            early = out_time_obj.time() < time(20, 0)

            if late or early:
                record["status"] = "H"
                record["amount"] = data["full_day_salary"] / 2
            else:
                record["status"] = "F"
                record["amount"] = data["full_day_salary"]
        elif entry:
            # record["status"] = "H"
            # record["amount"] = data["full_day_salary"] / 2
            pass

        daily_records.append(record)

    credit_qs = Staff_Credit.objects.filter(staff=data["staff"], date__range=[data["start_date"], data["end_date"]])

    context.update({


        "staff": data["staff"],
        "records": daily_records,
        "gross_salary": data["gross_salary"],
        "credit_total": data["credit_total"],
        "net_salary": data["net_salary"],
        "salary_value": data["monthly_salary"],
        "working_days": data["working_days"],
        "credits": credit_qs,
    })


    return render(request, "attendance_summary.html", context)

unit_map = {
    'FULL': FULL_UNITS,
    'HALF_MORNING': HALF_UNITS,
    'HALF_AFTERNOON': HALF_UNITS,
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

        status = "full" if total_units >= MAX_DAILY_UNITS else "available"
        status_by_date[day] = {"status": status}

    return JsonResponse({'year': year, 'month': month, 'days': status_by_date})


def calendar_leave_status_OLD(request):
    month_str = request.GET.get('month') or timezone.now().strftime('%Y-%m')
    year, month = map(int, month_str.split('-'))
    start_date = date(year, month, 1)
    end_date = date(year, month, monthrange(year, month)[1])
    leaves = StaffLeave.objects.filter(leave_date__range=(start_date, end_date), status='APPROVED')

    status_by_date = {}
    for day in range(1, end_date.day + 1):
        current = date(year, month, day)
        daily = leaves.filter(leave_date=current)
        full = daily.filter(leave_type='FULL').count()
        morning = daily.filter(leave_type='HALF_MORNING').count()
        afternoon = daily.filter(leave_type='HALF_AFTERNOON').count()

        status = "full" if full > 0 or (morning and afternoon) else "available"
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
    if approved_count < MAX_DAILY_UNITS:
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
            slot_count[lt] += FULL_UNITS
        else:
            slot_count[lt] += HALF_UNITS


        total_units += unit_map.get(lt, 0)

    available_units = MAX_DAILY_UNITS - total_units
    slots = []

    if available_units >= MAX_DAILY_UNITS:
        if slot_count['FULL'] < (MAX_DAILY_UNITS):
            slots.append("Full Day")
    if available_units >= HALF_UNITS:
        if slot_count['HALF_MORNING'] < (MAX_DAILY_UNITS * HALF_UNITS):
            slots.append("Half Morning")
        if slot_count['HALF_AFTERNOON'] < (MAX_DAILY_UNITS * HALF_UNITS):
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

            if monthly_used_units + current_unit > MAX_MONTHLY_UNITS_PER_USER:
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
                    slot_count[lt] += FULL_UNITS
                else:
                    slot_count[lt] += HALF_UNITS
                total_units += unit_map.get(lt, 0)

            available_units = MAX_DAILY_UNITS - total_units

            # Check if the requested slot is available
            slot_allowed = False
            if leave.leave_type == 'FULL':
                if available_units >= MAX_DAILY_UNITS and slot_count['FULL'] < MAX_DAILY_UNITS:
                    slot_allowed = True
            elif leave.leave_type == 'HALF_MORNING':
                if available_units >= HALF_UNITS and slot_count['HALF_MORNING'] < (MAX_DAILY_UNITS * HALF_UNITS):
                    slot_allowed = True
            elif leave.leave_type == 'HALF_AFTERNOON':
                if available_units >= HALF_UNITS and slot_count['HALF_AFTERNOON'] < (MAX_DAILY_UNITS * HALF_UNITS):
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
    monthly_remaining_units = MAX_MONTHLY_UNITS_PER_USER - monthly_used_units

    history = StaffLeave.objects.filter(staff_id=staff_id).order_by('-leave_date')

    selected_date_str = request.GET.get('date')
    selected_date = parse_date(selected_date_str) if selected_date_str else None

    return render(request, 'book_leave.html', {
        'form': form,
        'history': history,
        'staff': staff,
        'today': today,
        'monthly_remaining_units': monthly_remaining_units,
        'max_monthly_units': MAX_MONTHLY_UNITS_PER_USER,
        'selected_date': selected_date,
    })

def book_leave_OLD(request):
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

            month_start = leave.leave_date.replace(day=1)
            month_end = leave.leave_date.replace(day=monthrange(leave.leave_date.year, leave.leave_date.month)[1])

            approved_leaves = StaffLeave.objects.filter(
                staff_id=staff_id,
                leave_date__range=(month_start, month_end),
                status='APPROVED'
            )
            monthly_used_units = sum(unit_map.get(l.leave_type, 0) for l in approved_leaves)
            current_unit = unit_map.get(leave.leave_type, 0)

            if monthly_used_units + current_unit > MAX_MONTHLY_UNITS_PER_USER:
                messages.warning(request, f"Monthly limit reached ({monthly_used_units:.1f} used).")
                return redirect(f"{reverse('book_leave')}?{urlencode({'date': leave.leave_date})}")

            total_units_today = sum(unit_map.get(l.leave_type, 0) for l in
                                    StaffLeave.objects.filter(leave_date=leave.leave_date, status='APPROVED'))

            if total_units_today + current_unit > MAX_DAILY_UNITS:
                messages.warning(request, "Daily leave limit exceeded.")
                return redirect('book_leave')

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
    monthly_remaining_units = MAX_MONTHLY_UNITS_PER_USER - monthly_used_units

    history = StaffLeave.objects.filter(staff_id=staff_id).order_by('-leave_date')

    selected_date_str = request.GET.get('date')
    selected_date = parse_date(selected_date_str) if selected_date_str else None

    return render(request, 'book_leave.html', {
        'form': form,
        'history': history,
        'staff': staff,
        'today': today,
        'monthly_remaining_units': monthly_remaining_units,
        'max_monthly_units': MAX_MONTHLY_UNITS_PER_USER,
        'today': timezone.localdate(),  # for fallback
        'selected_date': selected_date,  # from ?date=YYYY-MM-DD or None
    })


def staff_profile(request):
    mobile = request.session.get('customer_mobile') or request.COOKIES.get('customer_mobile')
    if not mobile:
        return redirect('customer_login')

    staff = get_staff_by_mobile(mobile)
    if not staff:
        return redirect('home')

    return render(request, 'profile.html', {'staff': staff})
