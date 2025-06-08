from django.db import connection
from dashboard.models.dynamic_customer import DynamicCustomer

def get_customer_by_mobile(mobile):
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM customer_customer WHERE mobile = %s", [mobile])
        row = cursor.fetchone()
        if not row:
            return None
        columns = [col[0] for col in cursor.description]
        data = dict(zip(columns, row))
        return DynamicCustomer(**data)
