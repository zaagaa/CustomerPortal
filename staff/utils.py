from django.db import connection
from datetime import datetime, timedelta
from .models import Staff, StaffLeave, Staff_Credit

from datetime import datetime, date
from calendar import monthrange
from .models import Staff, StaffLeave, Staff_Credit
from django.db import models







def get_staff_by_mobile(mobile_number):
    """
    Returns staff row as a dictionary for a given mobile number.
    Only if 'discontinued' is 0.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM staff_staff WHERE mobile = %s AND discontinued = 0",
                [int(mobile_number)]  # Ensure proper type
            )
            row = cursor.fetchone()
            if row is None:
                return None
            columns = [col[0] for col in cursor.description]
            return dict(zip(columns, row))
    except Exception as e:
        print(f"[Error in get_staff_by_mobile] {e}")
        return None


def get_staff_name_by_id(staff_id):
    """
    Returns staff_name for a given staff UUID.
    """
    with connection.cursor() as cursor:
        cursor.execute("SELECT staff_name FROM staff_staff WHERE id = %s", [str(staff_id)])
        row = cursor.fetchone()
        return row[0] if row else f"ID: {staff_id}"