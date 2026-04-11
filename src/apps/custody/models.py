from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.core.models import TimeStampedModel


class AssetAssignment(TimeStampedModel):
    asset = models.ForeignKey(
        "inventory.Asset",
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="asset_assignments",
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="issued_assets",
        null=True,
        blank=True,
    )
    assigned_at = models.DateTimeField(default=timezone.now)
    returned_at = models.DateTimeField(null=True, blank=True)
    location_at_issue = models.CharField(max_length=150, blank=True)
    note = models.TextField(blank=True)
    is_current = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Закрепление ТМЦ"
        verbose_name_plural = "Закрепления ТМЦ"
        ordering = ["-assigned_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["asset"],
                condition=Q(is_current=True),
                name="unique_current_asset_assignment",
            )
        ]

    def __str__(self):
        return f"{self.asset} -> {self.employee}"


class TransferRequest(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "На согласовании"
        REJECTED = "rejected", "Отклонена"
        COMPLETED = "completed", "Завершена"

    asset = models.ForeignKey(
        "inventory.Asset",
        on_delete=models.CASCADE,
        related_name="transfer_requests",
    )
    from_employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="outgoing_transfer_requests",
    )
    to_employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="incoming_transfer_requests",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    comment = models.TextField(blank=True)
    requested_at = models.DateTimeField(default=timezone.now)
    processed_at = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="processed_transfer_requests",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Запрос на передачу"
        verbose_name_plural = "Запросы на передачу"
        ordering = ["-requested_at"]

    def __str__(self):
        return f"{self.asset} -> {self.to_employee}"
