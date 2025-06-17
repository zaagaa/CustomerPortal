from django.conf import settings
from django.contrib.auth.models import AbstractUser
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
    sync_offline = models.BigIntegerField(null=True, blank=True)
    sync_online = models.BigIntegerField(null=True, blank=True)

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


class Setting(models.Model):
    class Meta:
        db_table = 'setting_setting'
        managed = False  # External table, do not migrate

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    setting=models.CharField(max_length=100)
    value=models.CharField(max_length=1000)
    sync_offline = models.BigIntegerField(null=True, blank=True)
    sync_online = models.BigIntegerField(null=True, blank=True)


class Invoice(models.Model):
    class Meta:
        db_table = 'invoice_invoice'
        managed = False  # External table, do not migrate

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    invoice_date = models.DateTimeField(blank=True,null=True)
    invoice_number = models.IntegerField(default=0, null=True, blank=True)
    total_amount = models.FloatField(default=0, null=True, blank=True)
    discount = models.CharField(max_length=10, null=True, blank=True)
    discount_value = models.FloatField(default=None, null=True, blank=True)
    exchange_value = models.FloatField(default=None, null=True, blank=True)
    cash = models.FloatField(default=None, null=True, blank=True)
    card = models.FloatField(default=None, null=True, blank=True)
    upi = models.FloatField(default=None, null=True, blank=True)
    credit = models.FloatField(default=None, null=True, blank=True)
    headline = models.CharField(max_length=100, null=True, blank=True)
    round_off = models.FloatField(default=None, null=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.DO_NOTHING, null=True, blank=True, db_index=True)
    invoice_type = models.IntegerField(default=0, null=True, blank=True)
    cancel_no = models.IntegerField(default=None, null=True, blank=True)
    sync_offline = models.BigIntegerField(null=True, blank=True)
    sync_online = models.BigIntegerField(null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, null=True, blank=True,
                             db_index=True)

class User(AbstractUser):
    class Meta:
        db_table = 'authentication_user'  # existing table name
        managed = False  # do not try to create or modify it

    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    name = models.CharField(max_length=50, null=True, blank=True)
    position_choice = (
        (0, 'Super Admin'),
        (2, 'Billing'),
        (4, 'Purchase Entry'),
        (3, 'Customer Care'),
        (1, 'Administrator'),
    )
    position = models.IntegerField(default=0, null=True, choices=position_choice)
    ip_address = models.CharField(max_length=50, null=True, blank=True)
    raw_password = models.CharField(max_length=50, null=True, blank=True)
    dark_mode = models.IntegerField(default=0, null=True, blank=True)
    pos_statement_restriction = models.BooleanField(default=False)
    printer_name = models.CharField(max_length=100, null=True, blank=True)
    windows_printing = models.BooleanField(default=False)


class Profile(models.Model):
    class Meta:
        db_table = 'authentication_profile'  # existing table name
        managed = False  # do not try to create or modify it
    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    mobile = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)



    def __str__(self):
        return self.user.username