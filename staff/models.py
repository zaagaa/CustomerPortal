import uuid
from django.db import models

class StaffLeave(models.Model):
    LEAVE_TYPE_CHOICES = [
        ('FULL', 'Full Day'),
        ('HALF_MORNING', 'Half Day - Morning'),
        ('HALF_AFTERNOON', 'Half Day - Afternoon'),
    ]

    class Meta:
        db_table = 'staff_leave'
        managed = False  # External table, do not migrate

    id = models.UUIDField(primary_key=True, editable=False)
    staff_id = models.UUIDField(db_index=True)
    leave_date = models.DateField()
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPE_CHOICES, default='FULL')  # ✅ Add this
    reason = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=20)
    created_at = models.DateTimeField()
    sync_offline = models.BigIntegerField(null=True, blank=True)
    sync_online = models.BigIntegerField(null=True, blank=True)

class Attendance_Entry(models.Model):
    class Meta:
        db_table = 'staff_attendance_entry'
        managed = False
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    date = models.DateField(default=None, null=True, blank=True)
    staff= models.ForeignKey('Staff', on_delete=models.CASCADE, null=True, db_index=True)
    in_time=models.IntegerField(default=None, null=True, blank=True)
    out_time = models.IntegerField(default=None, null=True, blank=True)
    sync_offline = models.BigIntegerField(null=True, blank=True)
    sync_online = models.BigIntegerField(null=True, blank=True)



class Staff(models.Model):
    class Meta:
        db_table = 'staff_staff'
        managed = False

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    staff_name = models.CharField(max_length=50)
    join_date = models.DateField(default=None, null=True, blank=True)
    exit_date = models.DateField(default=None, null=True, blank=True)
    address = models.CharField(max_length=250, null=True, blank=True)
    city = models.CharField(max_length=50, null=True, blank=True)
    state = models.CharField(max_length=50, null=True, blank=True)
    country = models.CharField(max_length=50, null=True, blank=True)
    pincode = models.CharField(max_length=10, null=True, blank=True)
    mobile = models.BigIntegerField(default=None, null=True)
    remark = models.CharField(max_length=200, null=True, blank=True)
    salary = models.FloatField(default=None, null=True)
    dob = models.DateField(null=True, blank=True)
    discontinued = models.IntegerField(default=0, null=True, blank=True)
    biometric_code = models.CharField(max_length=50, null=True, blank=True)
    sync_offline = models.BigIntegerField(null=True, blank=True)
    sync_online = models.BigIntegerField(null=True, blank=True)

    # New fields
    epf_number = models.CharField(max_length=50, null=True, blank=True)
    esi_number = models.CharField(max_length=50, null=True, blank=True)
    aadhar_number = models.CharField(max_length=50, null=True, blank=True)


class Staff_Credit(models.Model):
    class Meta:
        db_table = 'staff_staff_credit'
        managed = False  # ✅ prevent Django from altering the table

    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.CharField(max_length=255, null=True, blank=True)
