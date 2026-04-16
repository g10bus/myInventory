from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.custody.models import TransferRequest
from apps.custody.services import issue_asset, request_transfer, return_asset
from apps.inventory.models import Asset
from apps.org.models import Department


class WebUserFlowsTestCase(TestCase):
    def setUp(self):
        self.department = Department.objects.create(
            name="IT отдел",
            code="IT",
            location="Офис 1",
        )
        self.admin = self._create_user(
            email="admin@example.com",
            password="StrongPass123!",
            last_name="Админов",
            first_name="Иван",
            office_location="Склад",
            is_staff=True,
        )
        self.employee = self._create_user(
            email="employee@example.com",
            password="StrongPass123!",
            last_name="Петров",
            first_name="Петр",
            office_location="Кабинет 101",
        )
        self.recipient = self._create_user(
            email="recipient@example.com",
            password="StrongPass123!",
            last_name="Сидоров",
            first_name="Сидор",
            office_location="Кабинет 202",
        )
        self.asset = Asset.objects.create(
            category="Ноутбук",
            title='Lenovo ThinkPad T14',
            model_name="Gen 4",
            inventory_number="INV-WEB-001",
            serial_number="SN-WEB-001",
            status=Asset.Status.RESERVE,
            location="Склад",
        )

    def _create_user(
        self,
        *,
        email,
        password,
        last_name,
        first_name,
        office_location,
        is_staff=False,
    ):
        return User.objects.create_user(
            username=email,
            email=email,
            password=password,
            last_name=last_name,
            first_name=first_name,
            role="Сотрудник",
            office_location=office_location,
            department=self.department,
            is_staff=is_staff,
        )

    def test_registration_and_login_user(self):
        registration_response = self.client.post(
            reverse("register"),
            {
                "email": "new.employee@example.com",
                "full_name": "Иванов Иван Иванович",
                "phone": "+7 900 000-00-00",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertRedirects(registration_response, reverse("home"))
        created_user = User.objects.get(email="new.employee@example.com")
        self.assertEqual(created_user.last_name, "Иванов")
        self.assertEqual(created_user.first_name, "Иван")
        self.assertEqual(created_user.middle_name, "Иванович")
        self.assertEqual(self.client.session.get("_auth_user_id"), str(created_user.pk))

        self.client.post(reverse("logout"))
        login_response = self.client.post(
            reverse("login"),
            {
                "email": "new.employee@example.com",
                "password": "StrongPass123!",
            },
        )

        self.assertRedirects(login_response, reverse("home"))
        self.assertEqual(self.client.session.get("_auth_user_id"), str(created_user.pk))

    def test_home_page_is_displayed_for_authorized_user(self):
        self.client.force_login(self.employee)

        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "main.html")
        self.assertContains(response, "Инвентаризация закрепленных материальных ценностей")
        self.assertContains(response, self.employee.full_name)

    def test_employee_can_get_list_of_assigned_assets(self):
        issue_asset(
            asset=self.asset,
            employee=self.employee,
            actor=self.admin,
            note="Выдано сотруднику для работы.",
        )
        self.client.force_login(self.employee)

        response = self.client.get(reverse("mytmc"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tmc.html")
        self.assertContains(response, self.asset.title)
        self.assertContains(response, self.asset.inventory_number)
        self.assertContains(response, self.employee.office_location)

    def test_employee_can_open_assigned_asset_details(self):
        issue_asset(
            asset=self.asset,
            employee=self.employee,
            actor=self.admin,
            note="Выдано сотруднику для просмотра карточки.",
        )
        self.client.force_login(self.employee)

        response = self.client.get(
            reverse("mytmc-detail", kwargs={"inventory_number": self.asset.inventory_number}),
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tmc_detail.html")
        self.assertContains(response, self.asset.title)
        self.assertContains(response, self.asset.inventory_number)
        self.assertContains(response, self.employee.short_name)

    def test_transfer_can_be_created_and_approved_via_web(self):
        issue_asset(
            asset=self.asset,
            employee=self.employee,
            actor=self.admin,
            note="Первичная выдача.",
        )
        self.client.force_login(self.employee)

        create_response = self.client.post(
            reverse("exchange"),
            {
                "action": "create_transfer",
                "asset_id": self.asset.pk,
                "recipient_id": self.recipient.pk,
                "comment": "Нужно передать оборудование коллеге.",
            },
        )

        self.assertRedirects(create_response, reverse("exchange"))
        transfer = TransferRequest.objects.get(asset=self.asset)
        self.assertEqual(transfer.status, TransferRequest.Status.PENDING)
        self.assertEqual(transfer.from_employee, self.employee)
        self.assertEqual(transfer.to_employee, self.recipient)

        self.client.force_login(self.recipient)
        approve_response = self.client.post(
            reverse("exchange"),
            {
                "action": "process_transfer",
                "transfer_id": transfer.pk,
                "decision": "approve",
            },
        )

        self.assertRedirects(approve_response, reverse("exchange"))
        transfer.refresh_from_db()
        self.asset.refresh_from_db()

        self.assertEqual(transfer.status, TransferRequest.Status.COMPLETED)
        self.assertEqual(transfer.processed_by, self.recipient)
        self.assertEqual(self.asset.current_assignment.employee, self.recipient)
        self.assertEqual(self.asset.location, self.recipient.office_location)

    def test_history_page_displays_operations_for_user(self):
        issue_asset(
            asset=self.asset,
            employee=self.employee,
            actor=self.admin,
            note="Выдано сотруднику.",
        )
        return_asset(
            asset=self.asset,
            actor=self.admin,
            note="Оборудование возвращено.",
            location="Склад",
        )
        self.client.force_login(self.employee)

        response = self.client.get(reverse("history"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "history.html")
        self.assertContains(response, self.asset.title)
        self.assertContains(response, "Выдача ТМЦ")
        self.assertContains(response, "Возврат ТМЦ")
        self.assertContains(response, "возвращено из закрепления сотрудника")


class WebPagesTestCase(TestCase):
    def setUp(self):
        self.department = Department.objects.create(
            name="Бэк-офис",
            code="BO",
            location="Офис 2",
        )
        self.admin = self._create_user(
            email="admin.pages@example.com",
            password="StrongPass123!",
            last_name="Смирнов",
            first_name="Алексей",
            office_location="Склад",
            is_staff=True,
        )
        self.employee = self._create_user(
            email="employee.pages@example.com",
            password="StrongPass123!",
            last_name="Орлов",
            first_name="Олег",
            office_location="Кабинет 305",
        )
        self.recipient = self._create_user(
            email="recipient.pages@example.com",
            password="StrongPass123!",
            last_name="Козлова",
            first_name="Анна",
            office_location="Кабинет 410",
        )
        self.asset = Asset.objects.create(
            category="Монитор",
            title="Dell P2723",
            model_name="27 inch",
            inventory_number="INV-PAGE-001",
            serial_number="SN-PAGE-001",
            status=Asset.Status.RESERVE,
            location="Склад",
        )
        issue_asset(
            asset=self.asset,
            employee=self.employee,
            actor=self.admin,
            note="Выдача для page-тестов.",
        )
        self.pending_transfer = request_transfer(
            asset=self.asset,
            from_employee=self.employee,
            to_employee=self.recipient,
            actor=self.employee,
            comment="Проверка страницы передачи.",
        )

    def _create_user(
        self,
        *,
        email,
        password,
        last_name,
        first_name,
        office_location,
        is_staff=False,
    ):
        return User.objects.create_user(
            username=email,
            email=email,
            password=password,
            last_name=last_name,
            first_name=first_name,
            role="Сотрудник",
            office_location=office_location,
            department=self.department,
            is_staff=is_staff,
        )

    def test_dashboard_page_is_rendered(self):
        self.client.force_login(self.employee)

        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "main.html")
        self.assertContains(response, "Инвентаризация закрепленных материальных ценностей")
        self.assertContains(response, self.asset.title)
        self.assertContains(response, "Закреплено за мной")

    def test_mytmc_page_is_rendered(self):
        self.client.force_login(self.employee)

        response = self.client.get(reverse("mytmc"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tmc.html")
        self.assertContains(response, "Материальные ценности сотрудника")
        self.assertContains(response, self.asset.title)
        self.assertContains(response, self.asset.inventory_number)

    def test_history_page_is_rendered(self):
        self.client.force_login(self.employee)

        response = self.client.get(reverse("history"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "history.html")
        self.assertContains(response, "История закрепления и передачи ТМЦ")
        self.assertContains(response, self.asset.title)
        self.assertContains(response, "Выдача ТМЦ")

    def test_exchange_page_is_rendered(self):
        self.client.force_login(self.employee)

        response = self.client.get(reverse("exchange"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "exchange.html")
        self.assertContains(response, "Запросы на передачу ТМЦ между сотрудниками")
        self.assertContains(response, self.asset.title)
        self.assertContains(response, self.recipient.short_name)

    def test_profile_page_is_rendered(self):
        self.client.force_login(self.employee)

        response = self.client.get(reverse("profile"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profile.html")
        self.assertContains(response, "Настройки профиля")
        self.assertContains(response, self.employee.email)
        self.assertContains(response, self.asset.title)

    def test_registration_page_is_rendered(self):
        response = self.client.get(reverse("register"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "register.html")
        self.assertContains(response, "Создание профиля")
        self.assertContains(response, "Зарегистрироваться")

    def test_login_page_is_rendered(self):
        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "login.html")
        self.assertContains(response, "МОЙ.ИНВЕНТАРЬ")
        self.assertContains(response, "Войти в систему")
