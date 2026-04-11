from apps.audit.models import AuditEvent


def log_event(*, event_type, actor=None, related_user=None, asset=None, message="", metadata=None):
    return AuditEvent.objects.create(
        event_type=event_type,
        actor=actor,
        related_user=related_user,
        asset=asset,
        message=message,
        metadata=metadata or {},
    )
