
from django.db.models import Q, Sum

from datetime import timezone as dt_timezone  # rename to avoid conflict

import pytz

from dashboard.models import Setting
from ..models import Staff, Staff_Credit, Attendance_Entry, StaffLeave

IST = pytz.timezone("Asia/Kolkata")

def get_ist_time_from_unix(ts):
    """Convert Unix timestamp to Asia/Kolkata localized time (safe for Django 5.2)"""
    utc_dt = datetime.fromtimestamp(ts, tz=dt_timezone.utc)  # ✅ use renamed dt_timezone
    return utc_dt.astimezone(IST)

from django.shortcuts import render
from django.utils import timezone
from datetime import date, datetime, time

import calendar

def staff_salary_OLD(staff_id, month=None):
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
            in_time_obj = get_ist_time_from_unix(entry.in_time).time()
            out_time_obj = get_ist_time_from_unix(entry.out_time).time()
            late = in_time_obj > time(10, 0)
            early = out_time_obj < time(20, 0)
            total_working_days += 0.5 if (late or early) else 1
        elif entry:
            # total_working_days += 0.5
            pass

    gross_salary = round(total_working_days * full_day_salary, 2)
    credit_total = Staff_Credit.objects.filter(
        staff=staff,
        date__range=[start_date, end_date]
    ).aggregate(total=Sum("amount"))["total"] or 0
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

    data = staff_salary(staff_id, dt.strftime("%Y%m"))
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

    # === Load Approved Leaves ===
    leave_qs = StaffLeave.objects.filter(
        staff_id=staff_id,
        status="APPROVED",
        leave_date__range=[data["start_date"], data["end_date"]],
    )

    leave_map = {}
    for lv in leave_qs:
        lt = lv.leave_type.upper()
        if lt == "FULL":
            leave_map[lv.leave_date] = "ABSENT"
        elif lt == "HALF_MORNING":
            leave_map.setdefault(lv.leave_date, set()).add("HALF - MORNING")
        elif lt == "HALF_AFTERNOON":
            leave_map.setdefault(lv.leave_date, set()).add("HALF - AFTERNOON")

    # Get incentive/penalty settings
    approved_incentive = int(Setting.objects.filter(setting='staff_approved_leave_incentive').values_list('value', flat=True).first() or 0)
    unapproved_penalty = int(Setting.objects.filter(setting='staff_unapproved_leave_penalty').values_list('value', flat=True).first() or 0)

    # Approved/unapproved counters
    approved_count = 0
    unapproved_count = 0

    total_incentive = 0
    total_penalty = 0
    final_incentive = 0
    # Rewrite records loop to include leave and incentives
    daily_records = []
    for day in range(1, data["loop_end_day"] + 1):
        current_date = data["dt"].replace(day=day).date()
        entry = data["attendance_map"].get(current_date)

        record = {
            "date": current_date,
            "in_time": None,
            "out_time": None,
            "status": "ABSENT - UNAPPROVED",
            "amount": 0,
            "approved": ""
        }

        if entry and entry.in_time and entry.out_time:
            in_time_obj = get_ist_time_from_unix(entry.in_time)
            out_time_obj = get_ist_time_from_unix(entry.out_time)

            record["in_time"] = in_time_obj.strftime("%I:%M %p")
            record["out_time"] = out_time_obj.strftime("%I:%M %p")

            late = in_time_obj.time() > time(10, 0)
            early = out_time_obj.time() < time(20, 0)

            if late:
                record["status"] = "HALF - MORNING"
                record["amount"] = data["full_day_salary"] / 2
            elif early:
                record["status"] = "HALF - AFTERNOON"
                record["amount"] = data["full_day_salary"] / 2
            else:
                record["status"] = "FULL DAY"
                record["amount"] = data["full_day_salary"]
        else:
            record["status"] = "ABSENT"
            record["amount"] = 0

        if Setting.objects.filter(setting='staff_leave_incentive_system').values_list('value', flat=True).first() == 'Enable':

            leave_status = leave_map.get(current_date)

            print(leave_status, "leave_status")

            if leave_status:
                if "ABSENT" in leave_status:
                    record["approved"] = "LEAVE APPROVED FOR FULL DAY"
                    approved_count += 1
                    record["status"] = "ABSENT"
                    record["amount"] = 0

                elif "HALF - MORNING" in leave_status:
                    record["approved"] = "LEAVE APPROVED FOR MORNING SESSION"
                    approved_count += 0.5
                    if record["status"] == "FULL DAY":
                        record["status"] = "HALF - AFTERNOON"
                        record["amount"] = data["full_day_salary"] / 2
                    if record["status"] == "HALF - MORNING":
                        record["status"] = "ABSENT"
                        record["amount"] = 0

                elif "HALF - AFTERNOON" in leave_status:
                    record["approved"] = "LEAVE APPROVED FOR AFTERNOON SESSION"
                    approved_count += 0.5
                    if record["status"] == "FULL DAY":
                        record["status"] = "HALF - AFTERNOON"
                        record["amount"] = data["full_day_salary"] / 2
                    if record["status"] == "HALF - AFTERNOON":
                        record["status"] = "ABSENT"
                        record["amount"] = 0

            else:
                cutoff_date = datetime.strptime("2025-06-12", "%Y-%m-%d").date()
                if current_date > cutoff_date: #THIS IS TMP CONDITION
                    if record["status"] == 'ABSENT':
                        unapproved_count += 1
                    elif record["status"] == 'FULL DAY':
                        pass
                    else:
                        unapproved_count += 0.5

            # Calculate totals
            total_incentive = approved_count * approved_incentive
            total_penalty = unapproved_count * unapproved_penalty
            final_incentive = total_incentive - total_penalty

        daily_records.append(record)

    print(final_incentive, data["net_salary"])

    data["net_salary"] = data["net_salary"] + final_incentive

    context.update({
        "staff": data["staff"],
        "records": daily_records,
        "gross_salary": data["gross_salary"],
        "credit_total": data["credit_total"],
        "net_salary": data["net_salary"],
        "salary_value": data["monthly_salary"],
        "working_days": data["working_days"],
        "credits": credit_qs,
        "approved_leave_count": approved_count,
        "unapproved_leave_count": unapproved_count,
        "approved_incentive": total_incentive,
        "unapproved_penalty": total_penalty,
        "final_incentive": final_incentive,
        "staff_leave_incentive_system": Setting.objects.filter(setting='staff_leave_incentive_system').values_list('value', flat=True).first()
    })

    return render(request, "attendance_summary.html", context)


def attendance_summary_OLD(request):
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