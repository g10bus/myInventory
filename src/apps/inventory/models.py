from django.db import models

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
