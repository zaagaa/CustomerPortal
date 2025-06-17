from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
from .models import Customer, Invoice, Profile
from dashboard.sms import send_otp_sms
from staff.utils import get_staff_by_mobile
import random
from dashboard.models import Point_Entry
from django.utils.timezone import localdate
from django.db import models
from django.utils.dateparse import parse_date
from django.db.models import Sum
from django.db.models.functions import TruncDate
from django.contrib.auth import get_user_model
# === Utility Functions ===

def get_customer_by_id(customer_id):
    try:
        return Customer.objects.get(id=customer_id)
    except Customer.DoesNotExist:
        return None


def get_customer_by_mobile(mobile):
    try:
        return Customer.objects.get(mobile=mobile)
    except Customer.DoesNotExist:
        return None


def is_super_user(request):
    mobile = request.session.get('customer_mobile') or request.COOKIES.get('customer_mobile')
    if not mobile:
        return False

    try:
        profile = Profile.objects.select_related('user').get(mobile=mobile)
        return profile.user.is_superuser
    except Profile.DoesNotExist:
        return False

def is_staff_user(request):
    mobile = request.session.get('customer_mobile') or request.COOKIES.get('customer_mobile')
    if not mobile:
        return False
    staff_record = get_staff_by_mobile(mobile)
    return staff_record is not None


def get_point_entries(customer_id):
    return Point_Entry.objects.filter(customer_id=customer_id) \
        .order_by('-entry_date')[:10] \
        .values('id', 'entry_date', 'point', 'balance', 'description')


# === View Functions ===

def customer_login(request):
    if request.method == 'POST':
        mobile = request.POST.get('mobile')
        customer = get_customer_by_mobile(mobile)

        if not customer:
            messages.error(request, "Mobile number not found.")
            return redirect('customer_login')

        otp = str(random.randint(100000, 999999))
        request.session['pending_customer_id'] = str(customer.id)
        request.session['pending_customer_mobile'] = mobile
        request.session['pending_otp'] = otp

        send_otp_sms(customer.customer_name, mobile, customer.point, otp)

        return redirect('verify_otp')

    return render(request, 'login.html')


def verify_otp(request):
    if request.method == 'POST':
        input_otp = request.POST.get('otp')
        session_otp = request.session.get('pending_otp')

        if input_otp == session_otp:
            response = redirect('dashboard_home')

            # Promote temporary session values
            customer_id = request.session.pop('pending_customer_id')
            customer_mobile = request.session.pop('pending_customer_mobile')
            request.session.pop('pending_otp', None)

            # Set login session
            request.session['customer_id'] = customer_id
            request.session['customer_mobile'] = customer_mobile

            # Set persistent cookies (valid for ~3 years)
            max_age = 60 * 60 * 24 * 3000
            response.set_cookie('customer_id', customer_id, max_age=max_age)
            response.set_cookie('customer_mobile', customer_mobile, max_age=max_age)

            return response

        messages.error(request, 'Invalid OTP')
        return redirect('verify_otp')

    return render(request, 'verify_otp.html')


def customer_logout(request):
    response = redirect('customer_login')
    request.session.flush()
    response.delete_cookie('customer_id')
    response.delete_cookie('customer_mobile')
    return response


def home(request):
    customer_id = request.session.get('customer_id')

    if not customer_id and 'customer_id' in request.COOKIES:
        customer_id = request.COOKIES['customer_id']
        request.session['customer_id'] = customer_id

    if not customer_id:
        return redirect('customer_login')

    customer = get_customer_by_id(customer_id)
    if not customer:
        return redirect('customer_login')

    point_entries = get_point_entries(customer_id)
    is_staff = is_staff_user(request)



    # Date filter for invoice total
    date_str = request.GET.get('date')
    selected_date = parse_date(date_str) if date_str else localdate()

    userwise_sales=0
    grand_total=0
    if is_super_user(request):
        # User-wise sales
        userwise_sales = (
            Invoice.objects
            .annotate(invoice_day=TruncDate('invoice_date'))
            .filter(invoice_day=selected_date)
            .values('user__id', 'user__username')
            .annotate(total_sales=Sum('total_amount'))
            .order_by('-total_sales')
        )



        # Grand total for the day
        grand_total = sum(row['total_sales'] or 0 for row in userwise_sales)

    context = {
        "customer": customer,
        "point_entries": point_entries,
        "is_staff": is_staff,
        "selected_date": selected_date,
        "userwise_sales": userwise_sales,
        "grand_total": grand_total,
        "is_super_user": is_super_user(request)
    }
    return render(request, 'home.html', context)
