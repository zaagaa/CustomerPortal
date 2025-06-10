from django.db import models
from django.utils import timezone
import uuid
from django.conf import settings

def current_unix_ms():
    import time
    return int(time.time() * 1000)

def initial_sync_offline():
    return current_unix_ms() if settings.INSTANCE_TYPE == 'offline' else None

def initial_sync_online():
    return current_unix_ms() if settings.INSTANCE_TYPE == 'online' else None


import uuid

class Deleted_Record(models.Model):
    class Meta:
        db_table = 'sync_deleted_record'
        managed = False
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # ✅ THIS LINE IS REQUIRED
    app_name = models.CharField(max_length=100, null=True, blank=True)
    model_name = models.CharField(max_length=100, null=True, blank=True)
    model_id = models.CharField(max_length=100, null=True, blank=True)
    deleted = models.IntegerField(default=0, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    sync_offline = models.BigIntegerField(null=True, blank=True, default=initial_sync_offline)
    sync_online = models.BigIntegerField(null=True, blank=True, default=initial_sync_online)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['model_name', 'model_id'], name='unique_model_entry')
        ]

    def __str__(self):
        return f"{self.app_name}.{self.model_name}({self.model_id})"




