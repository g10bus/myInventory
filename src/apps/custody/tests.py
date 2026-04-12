from django.test import TestCase

from apps.audit.models import AuditEvent
from apps.accounts.models import User
from apps.custody.models import AssetAssignment, TransferRequest
from apps.custody.services import (
    CustodyError,
    approve_transfer,
    issue_asset,
    reject_transfer,
    request_transfer,
    return_asset,
)
from apps.inventory.models import Asset
from apps.org.models import Department


class CustodyServicesTestCase(TestCase):
    def setUp(self):
        self.department = Department.objects.create(
            name="IT отдел",
            code="IT",
            location="Офис 1",
        )
        self.admin = self._create_user(
            email="admin@example.com",
            last_name="Админов",
            first_name="Иван",
            role="Администратор",
            office_location="Склад",
            is_staff=True,
        )
        self.employee = self._create_user(
            email="employee@example.com",
            last_name="Петров",
            first_name="Петр",
            office_location="Кабинет 101",
        )
        self.recipient = self._create_user(
            email="recipient@example.com",
            last_name="Сидоров",
            first_name="Сидор",
            office_location="Кабинет 202",
        )
        self.asset = self._create_asset()

    def _create_user(self, *, email, last_name, first_name, office_location, role="Сотрудник", is_staff=False):
        return User.objects.create_user(
            username=email,
            email=email,
            password="StrongPass123!",
            last_name=last_name,
            first_name=first_name,
            role=role,
            office_location=office_location,
            department=self.department,
            is_staff=is_staff,
        )

    def _create_asset(self):
        return Asset.objects.create(
            category="Ноутбук",
            title="Lenovo ThinkPad T14",
            model_name="Gen 4",
            inventory_number="INV-0001",
            serial_number="SN-0001",
            status=Asset.Status.RESERVE,
            location="Склад",
        )

    def test_issue_asset_to_employee(self):
        assignment = issue_asset(
            asset=self.asset,
            employee=self.employee,
            actor=self.admin,
            note="Выдача новому сотруднику.",
        )

        self.asset.refresh_from_db()

        self.assertEqual(assignment.employee, self.employee)
        self.assertEqual(assignment.assigned_by, self.admin)
        self.assertTrue(assignment.is_current)
        self.assertEqual(assignment.location_at_issue, self.employee.office_location)
        self.assertEqual(self.asset.status, Asset.Status.IN_USE)
        self.assertEqual(self.asset.location, self.employee.office_location)
        self.assertTrue(
            AuditEvent.objects.filter(
                event_type=AuditEvent.EventType.ASSET_ISSUED,
                asset=self.asset,
                related_user=self.employee,
            ).exists()
        )

    def test_prevent_duplicate_current_assignment_for_same_asset(self):
        issue_asset(
            asset=self.asset,
            employee=self.employee,
            actor=self.admin,
            note="Первичная выдача.",
        )

        with self.assertRaisesMessage(CustodyError, "ТМЦ уже закреплено за другим сотрудником."):
            issue_asset(
                asset=self.asset,
                employee=self.recipient,
                actor=self.admin,
                note="Повторная выдача.",
            )

        self.assertEqual(AssetAssignment.objects.filter(asset=self.asset, is_current=True).count(), 1)
        self.assertEqual(self.asset.assignments.get(is_current=True).employee, self.employee)

    def test_request_transfer_creates_pending_transfer(self):
        issue_asset(
            asset=self.asset,
            employee=self.employee,
            actor=self.admin,
            note="Выдано для дальнейшей передачи.",
        )

        transfer = request_transfer(
            asset=self.asset,
            from_employee=self.employee,
            to_employee=self.recipient,
            actor=self.admin,
            comment="Передача по заявке руководителя.",
        )

        self.assertEqual(transfer.status, TransferRequest.Status.PENDING)
        self.assertEqual(transfer.from_employee, self.employee)
        self.assertEqual(transfer.to_employee, self.recipient)
        self.assertEqual(transfer.asset, self.asset)
        self.assertTrue(
            AuditEvent.objects.filter(
                event_type=AuditEvent.EventType.TRANSFER_REQUESTED,
                asset=self.asset,
                related_user=self.recipient,
            ).exists()
        )

    def test_approve_transfer_reassigns_asset_to_recipient(self):
        original_assignment = issue_asset(
            asset=self.asset,
            employee=self.employee,
            actor=self.admin,
            note="Выдано сотруднику.",
        )
        transfer = request_transfer(
            asset=self.asset,
            from_employee=self.employee,
            to_employee=self.recipient,
            actor=self.admin,
            comment="Перемещение между сотрудниками.",
        )

        approve_transfer(transfer=transfer, actor=self.admin)

        transfer.refresh_from_db()
        original_assignment.refresh_from_db()
        self.asset.refresh_from_db()
        new_assignment = AssetAssignment.objects.get(asset=self.asset, is_current=True)

        self.assertEqual(transfer.status, TransferRequest.Status.COMPLETED)
        self.assertEqual(transfer.processed_by, self.admin)
        self.assertFalse(original_assignment.is_current)
        self.assertIsNotNone(original_assignment.returned_at)
        self.assertEqual(new_assignment.employee, self.recipient)
        self.assertEqual(new_assignment.assigned_by, self.admin)
        self.assertTrue(new_assignment.is_current)
        self.assertEqual(self.asset.status, Asset.Status.IN_USE)
        self.assertEqual(self.asset.location, self.recipient.office_location)
        self.assertTrue(
            AuditEvent.objects.filter(
                event_type=AuditEvent.EventType.TRANSFER_APPROVED,
                asset=self.asset,
                related_user=self.recipient,
            ).exists()
        )

    def test_reject_transfer_keeps_original_assignment(self):
        original_assignment = issue_asset(
            asset=self.asset,
            employee=self.employee,
            actor=self.admin,
            note="Выдано сотруднику.",
        )
        transfer = request_transfer(
            asset=self.asset,
            from_employee=self.employee,
            to_employee=self.recipient,
            actor=self.admin,
            comment="Передача на согласование.",
        )

        reject_transfer(transfer=transfer, actor=self.admin)

        transfer.refresh_from_db()
        original_assignment.refresh_from_db()
        self.asset.refresh_from_db()

        self.assertEqual(transfer.status, TransferRequest.Status.REJECTED)
        self.assertEqual(transfer.processed_by, self.admin)
        self.assertTrue(original_assignment.is_current)
        self.assertIsNone(original_assignment.returned_at)
        self.assertEqual(AssetAssignment.objects.filter(asset=self.asset, is_current=True).count(), 1)
        self.assertEqual(self.asset.current_assignment.employee, self.employee)
        self.assertEqual(self.asset.location, self.employee.office_location)
        self.assertTrue(
            AuditEvent.objects.filter(
                event_type=AuditEvent.EventType.TRANSFER_REJECTED,
                asset=self.asset,
            ).exists()
        )

    def test_return_asset_moves_it_to_reserve(self):
        assignment = issue_asset(
            asset=self.asset,
            employee=self.employee,
            actor=self.admin,
            note="Выдано сотруднику.",
        )

        return_asset(
            asset=self.asset,
            actor=self.admin,
            note="Оборудование возвращено на склад.",
            location="Склад 2",
        )

        assignment.refresh_from_db()
        self.asset.refresh_from_db()

        self.assertFalse(assignment.is_current)
        self.assertIsNotNone(assignment.returned_at)
        self.assertEqual(assignment.note, "Оборудование возвращено на склад.")
        self.assertEqual(self.asset.status, Asset.Status.RESERVE)
        self.assertEqual(self.asset.location, "Склад 2")
        self.assertEqual(AssetAssignment.objects.filter(asset=self.asset, is_current=True).count(), 0)
        self.assertTrue(
            AuditEvent.objects.filter(
                event_type=AuditEvent.EventType.ASSET_RETURNED,
                asset=self.asset,
                related_user=self.employee,
            ).exists()
        )
