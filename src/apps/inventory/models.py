from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel


class Asset(TimeStampedModel):
    class Status(models.TextChoices):
        IN_USE = "in_use", "В эксплуатации"
        REPAIR = "repair", "В ремонте"
        BROKEN = "broken", "Требует списания"
        RESERVE = "reserve", "В резерве"

    category = models.CharField(max_length=120)
    title = models.CharField(max_length=150)
    model_name = models.CharField(max_length=150, blank=True)
    inventory_number = models.CharField(max_length=50, unique=True)
    serial_number = models.CharField(max_length=80, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.IN_USE)
    location = models.CharField(max_length=150, blank=True)
    last_verified_at = models.DateField(null=True, blank=True)
    next_verification_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "ТМЦ"
        verbose_name_plural = "ТМЦ"
        ordering = ["category", "title", "inventory_number"]

    @property
    def current_assignment(self):
        prefetched = getattr(self, "current_assignments", None)
        if prefetched is not None:
            return prefetched[0] if prefetched else None
        return self.assignments.filter(is_current=True).select_related("employee").first()

    def __str__(self):
        return f"{self.title} ({self.inventory_number})"


class InventoryVerification(TimeStampedModel):
    asset = models.ForeignKey(
        "inventory.Asset",
        on_delete=models.CASCADE,
        related_name="verification_records",
    )
    verified_at = models.DateTimeField(default=timezone.now)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="inventory_verifications_completed",
        null=True,
        blank=True,
    )
    responsible_employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="inventory_verifications_as_responsible",
        null=True,
        blank=True,
    )
    location = models.CharField(max_length=150, blank=True)
    next_verification_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Фиксация инвентаризации"
        verbose_name_plural = "Фиксации инвентаризации"
        ordering = ["-verified_at", "-created_at"]

    def __str__(self):
        return f"Инвентаризация {self.asset.inventory_number} от {self.verified_at:%d.%m.%Y}"


class InventoryVerificationImage(TimeStampedModel):
    verification = models.ForeignKey(
        "inventory.InventoryVerification",
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField(upload_to="inventory_verifications/%Y/%m/%d/")
    caption = models.CharField(max_length=255, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = "Изображение инвентаризации"
        verbose_name_plural = "Изображения инвентаризации"
        ordering = ["sort_order", "created_at"]

    def __str__(self):
        return self.caption or f"Изображение для {self.verification}"

