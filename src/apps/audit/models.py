from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel


class AuditEvent(TimeStampedModel):
    class EventType(models.TextChoices):
        ASSET_ISSUED = "asset_issued", "Выдача ТМЦ"
        ASSET_RETURNED = "asset_returned", "Возврат ТМЦ"
        TRANSFER_REQUESTED = "transfer_requested", "Запрос на передачу"
        TRANSFER_APPROVED = "transfer_approved", "Передача подтверждена"
        TRANSFER_REJECTED = "transfer_rejected", "Передача отклонена"
        ASSET_VERIFIED = "asset_verified", "Сверка ТМЦ"
        ASSET_WRITTEN_OFF = "asset_written_off", "Списание ТМЦ"

    event_type = models.CharField(max_length=50, choices=EventType.choices)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events",
    )
    related_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="related_audit_events",
    )
    asset = models.ForeignKey(
        "inventory.Asset",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events",
    )
    message = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    occurred_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Событие аудита"
        verbose_name_plural = "События аудита"
        ordering = ["-occurred_at"]

    def __str__(self):
        return self.message
