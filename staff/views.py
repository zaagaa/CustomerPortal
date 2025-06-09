from django.shortcuts import render, redirect
from staff.utils import get_staff_by_mobile

def staff_profile(request):
    mobile = request.session.get('customer_mobile') or request.COOKIES.get('customer_mobile')
    if not mobile:
        return redirect('customer_login')  # Or show 403

    staff = get_staff_by_mobile(mobile)
    if not staff:
        return redirect('home')  # Or show "You are not staff"

    return render(request, 'profile.html', {'staff': staff})
