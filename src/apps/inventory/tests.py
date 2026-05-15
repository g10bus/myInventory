from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import User
from apps.inventory.ui import resolve_inventory_window
from apps.org.models import Department

from .models import EmployeeInventoryAssignment


class InventoryUiTestCase(TestCase):
    def setUp(self):
        self.department = Department.objects.create(
            name="IT отдел",
            code="IT",
            location="Офис 1",
        )
        self.admin = self._create_user(
            email="admin@example.com",
            first_name="Иван",
            last_name="Админов",
            is_staff=True,
        )
        self.employee = self._create_user(
            email="employee@example.com",
            first_name="Петр",
            last_name="Петров",
        )

    def _create_user(self, *, email, first_name, last_name, is_staff=False):
        return User.objects.create_user(
            username=email,
            email=email,
            password="StrongPass123!",
            first_name=first_name,
            last_name=last_name,
            department=self.department,
            is_staff=is_staff,
        )

    def test_resolve_inventory_window_returns_default_state_without_assignments(self):
        result = resolve_inventory_window(self.employee)

        self.assertFalse(result["verification_allowed"])
        self.assertIsNone(result["active_inventory_assignment"])
        self.assertIsNone(result["upcoming_inventory_assignment"])
        self.assertIn("Инвентаризация пока не назначена", result["verification_lock_message"])

    def test_resolve_inventory_window_returns_upcoming_assignment_context(self):
        today = timezone.localdate()
        assignment = EmployeeInventoryAssignment.objects.create(
            employee=self.employee,
            assigned_by=self.admin,
            date_from=today + timedelta(days=3),
            date_to=today + timedelta(days=7),
        )

        result = resolve_inventory_window(self.employee)

        self.assertFalse(result["verification_allowed"])
        self.assertIsNone(result["active_inventory_assignment"])
        self.assertEqual(result["upcoming_inventory_assignment"], assignment)
        self.assertIn(assignment.date_from.strftime("%d.%m.%Y"), result["verification_lock_message"])

    def test_resolve_inventory_window_returns_active_assignment_context(self):
        today = timezone.localdate()
        active_assignment = EmployeeInventoryAssignment.objects.create(
            employee=self.employee,
            assigned_by=self.admin,
            date_from=today - timedelta(days=1),
            date_to=today + timedelta(days=1),
        )
        upcoming_assignment = EmployeeInventoryAssignment.objects.create(
            employee=self.employee,
            assigned_by=self.admin,
            date_from=today + timedelta(days=10),
            date_to=today + timedelta(days=12),
        )

        result = resolve_inventory_window(self.employee)

        self.assertTrue(result["verification_allowed"])
        self.assertEqual(result["active_inventory_assignment"], active_assignment)
        self.assertEqual(result["upcoming_inventory_assignment"], upcoming_assignment)
        self.assertEqual(result["verification_lock_message"], "")
