from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.core.models import TimeStampedModel


class User(AbstractUser, TimeStampedModel):
    email = models.EmailField(unique=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    middle_name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=50, blank=True, default="Сотрудник")
    position = models.CharField(max_length=150, blank=True)
    office_location = models.CharField(max_length=150, blank=True)
    department = models.ForeignKey(
        "org.Department",
        on_delete=models.SET_NULL,
        related_name="employees",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"
        ordering = ["last_name", "first_name", "email"]

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.email
        super().save(*args, **kwargs)

    @property
    def full_name(self):
        parts = [self.last_name, self.first_name, self.middle_name]
        return " ".join(part for part in parts if part).strip() or self.email

    @property
    def short_name(self):
        initials = []
        if self.first_name:
            initials.append(f"{self.first_name[0]}.")
        if self.middle_name:
            initials.append(f"{self.middle_name[0]}.")
        if self.last_name:
            return " ".join([self.last_name, *initials]).strip()
        return self.email

    @property
    def initial(self):
        if self.first_name:
            return self.first_name[0]
        return self.email[0] if self.email else "?"

    @property
    def is_administrator(self):
        if self.is_superuser or self.is_staff:
            return True
        if not self.pk:
            return False
        return self.groups.filter(name__in=["system_admin", "inventory_operator"]).exists()

    def __str__(self):
        return self.full_name
