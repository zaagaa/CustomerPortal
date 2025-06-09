from django.shortcuts import render, redirect
from django.contrib import messages
from dashboard.db import get_customer_by_mobile, get_customer_by_id
import random
from django.db import connection
from dashboard.sms import send_otp_sms
from staff.utils import get_staff_by_mobile

def is_staff_user(request):
    mobile = request.session.get('customer_mobile') or request.COOKIES.get('customer_mobile')
    if not mobile:
        return False
    staff_record = get_staff_by_mobile(mobile)
    return staff_record is not None

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
        if input_otp == request.session.get('pending_otp'):
            response = redirect('dashboard_home')

            # Set login info in session
            customer_id = request.session.pop('pending_customer_id')
            customer_mobile = request.session.pop('pending_customer_mobile')

            request.session['customer_id'] = customer_id
            request.session['customer_mobile'] = customer_mobile

            # Set persistent cookie (expires in 30 days)
            response.set_cookie('customer_id', customer_id, max_age=60*60*24*3000)
            response.set_cookie('customer_mobile', customer_mobile, max_age=60 * 60 * 24 * 3000)
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

def get_point_entries(customer_id):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, entry_date, point, balance, description
            FROM invoice_point_entry
            WHERE customer_id = %s
            ORDER BY entry_date DESC
            LIMIT 10
        """, [customer_id])
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in rows]



def home(request):
    customer_id = request.session.get('customer_id')

    # Try to restore from cookie if session expired
    if not customer_id and 'customer_id' in request.COOKIES:
        request.session['customer_id'] = request.COOKIES['customer_id']
        customer_id = request.COOKIES['customer_id']

    if not customer_id:
        return redirect('customer_login')

    customer = get_customer_by_id(customer_id)
    point_entries = get_point_entries(customer_id)
    is_staff = is_staff_user(request)

    context = {
        "customer": customer,
        "point_entries": point_entries,
        "is_staff": is_staff
    }

    return render(request, 'home.html', context)



