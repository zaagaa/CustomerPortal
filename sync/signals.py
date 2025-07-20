
from django.db.models.signals import pre_delete
from sync.utils import log_deleted_instance
from django.conf import settings
import time
from django.db.models.signals import pre_save
from django.dispatch import receiver


@receiver(pre_delete)
def log_all_deletions(sender, instance, **kwargs):
    # Avoid logging system model deletions (or your own log table)
    EXCLUDE_APPS = {'admin', 'auth', 'contenttypes', 'sessions', 'sync'}
    if sender._meta.app_label in EXCLUDE_APPS:
        return
    try:
        log_deleted_instance(instance)
    except Exception as e:
        print(f"❌ Failed to log deletion of {sender.__name__}({instance.pk}): {e}")



@receiver(pre_save)
def update_sync_unix_globally(sender, instance, **kwargs):
    if sender._meta.app_label in ['admin', 'auth', 'contenttypes', 'sessions']:
        return

    def current_unix_ms():
        return int(time.time() * 1000)

    now_ms = current_unix_ms()
    if hasattr(instance, 'sync_offline') and settings.INSTANCE_TYPE == 'offline':
        instance.sync_offline = now_ms

    if hasattr(instance, 'sync_online') and settings.INSTANCE_TYPE == 'online':
        instance.sync_online = now_ms

    print(f"🔁 Updating sync field for {sender.__name__} | Mode: {settings.INSTANCE_TYPE}")