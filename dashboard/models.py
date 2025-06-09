from django.utils import timezone
import uuid

from django.db import models

class Customer(models.Model):
    class Meta:
        db_table = 'customer_customer'
        managed = False  # External table, do not migrate

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    customer_name=models.CharField(max_length=50)
    tax_number=models.CharField(max_length=50, null=True, blank=True)
    address=models.CharField(max_length=250, null=True, blank=True)
    city = models.CharField(max_length=50, null=True, blank=True)
    state = models.CharField(max_length=50, null=True, blank=True)
    country = models.CharField(max_length=50, null=True, blank=True)
    pincode = models.CharField(max_length=10, null=True, blank=True)
    mobile = models.BigIntegerField(unique=True, null=True, blank=True)
    point = models.FloatField(default=0, null=True, blank=True)
    # sync_offline = models.BigIntegerField(null=True, blank=True)
    # sync_online = models.BigIntegerField(null=True, blank=True)

class Point_Entry(models.Model):
    class Meta:
        db_table = 'invoice_point_entry'
        managed = False  # External table, do not migrate
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    customer=models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, db_index=True)
    entry_date = models.DateTimeField(default=timezone.now, blank=True)
    point = models.FloatField(default=0, null=True, blank=True)
    balance = models.FloatField(default=0, null=True, blank=True)
    description = models.CharField(max_length=75, null=True, blank=True)
