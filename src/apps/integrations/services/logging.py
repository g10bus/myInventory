from django.utils import timezone

from apps.integrations.models import IntegrationSyncLog


def start_log(*, integration_type, action, triggered_by=None, details=None):
    return IntegrationSyncLog.objects.create(
        integration_type=integration_type,
        action=action,
        status=IntegrationSyncLog.Status.RUNNING,
        triggered_by=triggered_by,
        details=details or {},
    )


def finish_log(log, *, status, message="", details=None):
    log.status = status
    log.message = message
    if details is not None:
        log.details = details
    log.finished_at = timezone.now()
    log.save(update_fields=["status", "message", "details", "finished_at", "updated_at"])
    return log

