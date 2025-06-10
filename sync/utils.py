
from sync.models import Deleted_Record


def log_deleted_instance(instance):
    """
    Record deleted instance metadata in Deleted_Record.
    """
    model = type(instance)
    Deleted_Record.objects.create(
        app_name=model._meta.app_label,
        model_name=model._meta.object_name,
        model_id=str(instance.pk)
    )
    print(f"🗑️ Logged: {model._meta.app_label}.{model._meta.object_name}({instance.pk})")
