from datetime import date

from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.custody.models import TransferRequest
from apps.custody.services import issue_asset, request_transfer, return_asset
from apps.inventory.models import Asset, InventoryVerification
from apps.inventory.services import record_verification
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

    def _build_user_admin_payload(self, user, **overrides):
        payload = {
            "email": user.email,
            "last_name": user.last_name,
            "first_name": user.first_name,
            "middle_name": user.middle_name,
            "phone": user.phone,
            "role": user.role,
            "position": user.position,
            "office_location": user.office_location,
            "department": user.department_id or "",
            "blocked_user": "" if user.is_active else "on",
        }
        payload.update(overrides)
        return payload

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

    def test_asset_detail_displays_verification_fixations(self):
        issue_asset(
            asset=self.asset,
            employee=self.employee,
            actor=self.admin,
            note="Выдано сотруднику для проверки карточки.",
        )
        verification = record_verification(
            asset=self.asset,
            actor=self.admin,
            next_verification_date=date(2026, 6, 12),
            note="Проверен комплект, маркировка и фактическая локация ТМЦ.",
        )
        self.client.force_login(self.employee)

        response = self.client.get(
            reverse("mytmc-detail", kwargs={"inventory_number": self.asset.inventory_number}),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(InventoryVerification.objects.filter(asset=self.asset).count(), 1)
        self.assertEqual(verification.responsible_employee, self.employee)
        self.assertEqual(verification.location, self.employee.office_location)
        self.assertContains(response, "Фиксации последних инвентаризаций")
        self.assertContains(response, "Проверен комплект, маркировка и фактическая локация ТМЦ.")
        self.assertContains(response, self.admin.full_name)
        self.assertContains(response, self.employee.full_name)
        self.assertContains(response, self.employee.office_location)
        self.assertContains(response, "12.06.2026")

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

    def _build_user_admin_payload(self, user, **overrides):
        payload = {
            "email": user.email,
            "last_name": user.last_name,
            "first_name": user.first_name,
            "middle_name": user.middle_name,
            "phone": user.phone,
            "role": user.role,
            "position": user.position,
            "office_location": user.office_location,
            "department": user.department_id or "",
            "blocked_user": "" if user.is_active else "on",
        }
        payload.update(overrides)
        return payload

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

    def test_mytmc_filters_by_category(self):
        extra_asset = Asset.objects.create(
            category="РќРѕСѓС‚Р±СѓРє",
            title="HP EliteBook",
            model_name="840 G9",
            inventory_number="INV-PAGE-002",
            serial_number="SN-PAGE-002",
            status=Asset.Status.IN_USE,
            location="РћС„РёСЃ 2",
        )
        issue_asset(
            asset=extra_asset,
            employee=self.employee,
            actor=self.admin,
            note="Р’С‹РґР°С‡Р° РґР»СЏ С„РёР»СЊС‚СЂР°С†РёРё.",
        )
        self.client.force_login(self.employee)

        response = self.client.get(reverse("mytmc"), {"category": self.asset.category})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.asset.title)
        self.assertNotContains(response, extra_asset.title)

    def test_inventory_admin_filters_by_category(self):
        extra_asset = Asset.objects.create(
            category="РќРѕСѓС‚Р±СѓРє",
            title="MacBook Pro",
            model_name="14",
            inventory_number="INV-PAGE-003",
            serial_number="SN-PAGE-003",
            status=Asset.Status.RESERVE,
            location="РЎРєР»Р°Рґ",
        )
        self.client.force_login(self.admin)

        response = self.client.get(reverse("asset-admin"), {"category": self.asset.category})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.asset.title)
        self.assertNotContains(response, extra_asset.title)

    def test_inventory_admin_filters_by_employee_location_and_verification_date(self):
        self.asset.next_verification_date = date(2026, 5, 20)
        self.asset.save(update_fields=["next_verification_date"])

        extra_asset = Asset.objects.create(
            category="Принтер",
            title="HP LaserJet",
            model_name="M404",
            inventory_number="INV-PAGE-004",
            serial_number="SN-PAGE-004",
            status=Asset.Status.IN_USE,
            location="Склад",
            next_verification_date=date(2026, 6, 15),
        )
        issue_asset(
            asset=extra_asset,
            employee=self.recipient,
            actor=self.admin,
            note="Выдача для проверки фильтров админа.",
        )
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("asset-admin"),
            {
                "employee": str(self.employee.pk),
                "location": self.employee.office_location,
                "verification_date_from": "2026-05-01",
                "verification_date_to": "2026-05-31",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.asset.title)
        self.assertNotContains(response, extra_asset.title)

    def test_user_admin_filters_by_status_and_admin_access(self):
        admin_group = Group.objects.create(name="system_admin")
        self.employee.groups.add(admin_group)
        self.recipient.is_active = False
        self.recipient.save(update_fields=["is_active"])
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("user-admin"),
            {
                "activity": "inactive",
                "admin_access": "regular",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.recipient.email)
        self.assertNotContains(response, self.employee.email)

    def test_user_admin_filters_by_assets_count_range(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("user-admin"),
            {
                "assets_count_from": "1",
                "assets_count_to": "1",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.employee.email)
        self.assertNotContains(response, self.recipient.email)

    def test_regular_user_does_not_see_switch_mode_button(self):
        self.client.force_login(self.employee)

        response = self.client.get(reverse("profile"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, reverse("switch-ui-mode"))
        self.assertNotContains(response, reverse("asset-admin"))

    def legacy_test_admin_can_switch_interface_mode(self):
        self.client.force_login(self.admin)

        default_response = self.client.get(reverse("profile"))
        self.assertContains(default_response, reverse("switch-ui-mode"))
        self.assertNotContains(default_response, reverse("asset-admin"))

        switch_response = self.client.post(
            reverse("switch-ui-mode"),
            {
                "mode": "admin",
                "next": reverse("profile"),
            },
        )

        self.assertRedirects(switch_response, reverse("profile"))
        self.assertEqual(self.client.session.get("ui_mode"), "admin")

        admin_response = self.client.get(reverse("profile"))
        self.assertContains(admin_response, reverse("asset-admin"))
        self.assertContains(admin_response, "Перейти в обычный режим")

    def test_regular_user_cannot_switch_to_admin_mode(self):
        self.client.force_login(self.employee)

        response = self.client.post(reverse("switch-ui-mode"), {"mode": "admin"})

        self.assertEqual(response.status_code, 403)
        self.assertNotEqual(self.client.session.get("ui_mode"), "admin")

    def test_admin_can_open_mode_confirmation_page(self):
        self.client.force_login(self.admin)

        profile_response = self.client.get(reverse("profile"))

        self.assertEqual(profile_response.status_code, 200)
        self.assertContains(profile_response, reverse("confirm-admin-ui-mode"))
        self.assertNotContains(profile_response, reverse("asset-admin"))

        confirm_response = self.client.get(
            reverse("confirm-admin-ui-mode"),
            {
                "next": reverse("profile"),
            },
        )

        self.assertEqual(confirm_response.status_code, 200)
        self.assertTemplateUsed(confirm_response, "confirm_admin_mode.html")
        self.assertContains(confirm_response, "Подтвердите пароль")

    def test_admin_can_switch_interface_mode_after_password_confirmation(self):
        self.client.force_login(self.admin)

        switch_response = self.client.post(
            reverse("confirm-admin-ui-mode"),
            {
                "password": "StrongPass123!",
                "next": reverse("profile"),
            },
        )

        self.assertRedirects(switch_response, reverse("profile"))
        self.assertEqual(self.client.session.get("ui_mode"), "admin")

        admin_response = self.client.get(reverse("profile"))
        self.assertContains(admin_response, reverse("asset-admin"))
        self.assertContains(admin_response, "РџРµСЂРµР№С‚Рё РІ РѕР±С‹С‡РЅС‹Р№ СЂРµР¶РёРј")

    def test_admin_cannot_switch_interface_mode_with_invalid_password(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("confirm-admin-ui-mode"),
            {
                "password": "WrongPass123!",
                "next": reverse("profile"),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "confirm_admin_mode.html")
        self.assertContains(response, "Указан неверный пароль.")
        self.assertNotEqual(self.client.session.get("ui_mode"), "admin")

    def test_regular_user_cannot_open_admin_mode_confirmation_page(self):
        self.client.force_login(self.employee)

        response = self.client.get(reverse("confirm-admin-ui-mode"))

        self.assertEqual(response.status_code, 403)

    def test_admin_can_grant_admin_access_to_other_user(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("user-edit", kwargs={"user_id": self.employee.pk}),
            self._build_user_admin_payload(
                self.employee,
                administrator_access="on",
            ),
        )

        self.assertRedirects(response, reverse("user-admin"))
        self.employee.refresh_from_db()
        self.assertTrue(self.employee.is_administrator)
        self.assertTrue(self.employee.groups.filter(name="system_admin").exists())

    def test_admin_can_revoke_admin_access_from_other_user(self):
        admin_group = Group.objects.create(name="system_admin")
        self.employee.groups.add(admin_group)
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("user-edit", kwargs={"user_id": self.employee.pk}),
            self._build_user_admin_payload(self.employee),
        )

        self.assertRedirects(response, reverse("user-admin"))
        self.employee.refresh_from_db()
        self.assertFalse(self.employee.groups.filter(name="system_admin").exists())

    def test_admin_can_block_user(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("user-edit", kwargs={"user_id": self.employee.pk}),
            self._build_user_admin_payload(
                self.employee,
                blocked_user="on",
            ),
        )

        self.assertRedirects(response, reverse("user-admin"))
        self.employee.refresh_from_db()
        self.assertFalse(self.employee.is_active)

    def test_blocked_user_cannot_login(self):
        self.employee.is_active = False
        self.employee.save(update_fields=["is_active"])

        response = self.client.post(
            reverse("login"),
            {
                "email": self.employee.email,
                "password": "StrongPass123!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "login.html")
        self.assertIsNone(self.client.session.get("_auth_user_id"))

    def test_blocked_user_is_logged_out_from_active_session(self):
        self.client.force_login(self.employee)
        self.employee.is_active = False
        self.employee.save(update_fields=["is_active"])

        response = self.client.get(reverse("home"))

        self.assertRedirects(response, reverse("login"))
        self.assertIsNone(self.client.session.get("_auth_user_id"))

    def test_admin_cannot_manage_self_in_user_admin(self):
        self.client.force_login(self.admin)

        list_response = self.client.get(reverse("user-admin"))
        edit_response = self.client.get(reverse("user-edit", kwargs={"user_id": self.admin.pk}))

        self.assertEqual(list_response.status_code, 200)
        self.assertNotContains(list_response, reverse("user-edit", kwargs={"user_id": self.admin.pk}))
        self.assertEqual(edit_response.status_code, 404)

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
