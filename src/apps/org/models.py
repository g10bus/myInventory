from django.db import models

from apps.core.models import TimeStampedModel


class Location(TimeStampedModel):
    name = models.CharField(max_length=150, unique=True)
    code = models.CharField(max_length=30, blank=True)
    address = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "Локация"
        verbose_name_plural = "Локации"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Department(TimeStampedModel):
    name = models.CharField(max_length=150, unique=True)
    code = models.CharField(max_length=30, blank=True)
    location = models.CharField(max_length=150, blank=True)

    class Meta:
        verbose_name = "Отдел"
        verbose_name_plural = "Отделы"
        ordering = ["name"]

    def __str__(self):
        return self.name
