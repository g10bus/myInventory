from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import authenticate
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.integrations.models import (
    ActiveDirectorySettings,
    IntegrationSyncLog,
    OneCIntegrationSettings,
)
from apps.integrations.services.one_c import sync_one_c_data
from apps.inventory.models import Asset
from apps.org.models import Department


class IntegrationsTestCase(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin@example.com",
            email="admin@example.com",
            password="StrongPass123!",
            first_name="Иван",
            last_name="Админов",
            is_staff=True,
        )
        self.employee = User.objects.create_user(
            username="employee@example.com",
            email="employee@example.com",
            password="StrongPass123!",
            first_name="Петр",
            last_name="Петров",
        )

    def test_admin_can_open_integrations_admin_page(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("integrations-admin"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "1С и Active Directory")

    def test_regular_user_cannot_open_integrations_admin_page(self):
        self.client.force_login(self.employee)

        response = self.client.get(reverse("integrations-admin"))

        self.assertEqual(response.status_code, 403)

    @patch("apps.integrations.services.one_c._load_requests")
    @patch("apps.integrations.services.one_c.OneCClient.get_json")
    def test_one_c_sync_imports_departments_users_and_assets(self, mocked_get_json, mocked_load_requests):
        OneCIntegrationSettings.objects.create(
            enabled=True,
            base_url="https://1c.local/api/",
        )
        mocked_load_requests.return_value = SimpleNamespace(
            Session=lambda: SimpleNamespace(headers={}, auth=None)
        )
        mocked_get_json.side_effect = [
            [
                {
                    "name": "IT отдел",
                    "code": "IT",
                    "location": "Офис 1",
                }
            ],
            [
                {
                    "email": "new.employee@example.com",
                    "first_name": "Анна",
                    "last_name": "Сидорова",
                    "middle_name": "Игоревна",
                    "department": "IT отдел",
                    "position": "Системный аналитик",
                    "location": "Офис 1",
                }
            ],
            [
                {
                    "inventory_number": "INV-1C-001",
                    "category": "Ноутбук",
                    "title": "Lenovo ThinkPad",
                    "model_name": "T14",
                    "serial_number": "SN-1C-001",
                    "status": "issued",
                    "location": "Офис 1",
                }
            ],
        ]

        result = sync_one_c_data(actor=self.admin)

        self.assertEqual(result["departments"], 1)
        self.assertEqual(result["employees"], 1)
        self.assertEqual(result["assets"], 1)
        self.assertTrue(Department.objects.filter(name="IT отдел").exists())
        imported_user = User.objects.get(email="new.employee@example.com")
        self.assertEqual(imported_user.position, "Системный аналитик")
        self.assertEqual(imported_user.department.name, "IT отдел")
        self.assertTrue(Asset.objects.filter(inventory_number="INV-1C-001").exists())
        self.assertTrue(
            IntegrationSyncLog.objects.filter(
                integration_type=IntegrationSyncLog.IntegrationType.ONE_C,
                status=IntegrationSyncLog.Status.SUCCESS,
            ).exists()
        )

    def test_active_directory_backend_authenticates_and_creates_local_user(self):
        ActiveDirectorySettings.objects.create(
            enabled=True,
            server_uri="dc01.company.local",
            domain="COMPANY",
            base_dn="DC=company,DC=local",
            sync_profile_on_login=True,
        )

        class FakeConnection:
            def __init__(self, *args, **kwargs):
                self.entries = []

            def search(self, base_dn, search_filter, attributes=None):
                self.entries = [
                    {
                        "mail": "ldap.user@company.local",
                        "givenName": "Илья",
                        "sn": "Иванов",
                        "middleName": "Олегович",
                        "department": "Служба поддержки",
                        "title": "Инженер",
                        "physicalDeliveryOfficeName": "Офис 3",
                        "displayName": "Иванов Илья Олегович",
                    }
                ]
                return True

        fake_ldap3 = SimpleNamespace(
            NONE=object(),
            Server=lambda *args, **kwargs: object(),
            Connection=FakeConnection,
        )

        with patch("apps.integrations.services.active_directory._load_ldap3", return_value=fake_ldap3):
            user = authenticate(
                username="ldap.user@company.local",
                email="ldap.user@company.local",
                password="Secret123!",
            )

        self.assertIsNotNone(user)
        self.assertEqual(user.email, "ldap.user@company.local")
        self.assertEqual(user.first_name, "Илья")
        self.assertEqual(user.last_name, "Иванов")
        self.assertEqual(user.position, "Инженер")
        self.assertEqual(user.department.name, "Служба поддержки")
