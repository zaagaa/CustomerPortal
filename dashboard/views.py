from django.shortcuts import render, redirect
from django.contrib import messages
from dashboard.db import get_customer_by_mobile

def customer_login(request):
    if request.method == 'POST':
        mobile = request.POST.get('mobile')
        customer = get_customer_by_mobile(mobile)

        if customer:
            request.session['customer_id'] = str(customer.id)
            request.session['customer_name'] = customer.customer_name
            request.session['customer_mobile'] = customer.mobile
            request.session['customer_point'] = customer.point
            request.session['customer_address'] = customer.address
            return redirect('dashboard_home')

        else:
            messages.error(request, 'Mobile number not found')
            return redirect('customer_login')
    return render(request, 'login.html')


def customer_logout(request):
    request.session.flush()
    return redirect('customer_login')


def home(request):
    customer_id = request.session.get('customer_id')
    customer_name = request.session.get('customer_name')

    if not customer_id:
        return redirect('customer_login')

    # You already have mobile-based login, now let's get more info
    mobile = request.session.get('customer_mobile')  # optional
    customer = {
        'name': request.session.get('customer_name'),
        'mobile': request.session.get('customer_mobile'),
        'point': request.session.get('customer_point'),
        'address': request.session.get('customer_address'),
    }

    return render(request, 'home.html', {'customer': customer})



