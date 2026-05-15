from django import forms

from .models import ActiveDirectorySettings, OneCIntegrationSettings


class RetainedSecretModelForm(forms.ModelForm):
    retained_secret_fields = ()

    def save(self, commit=True):
        for field_name in self.retained_secret_fields:
            if self.instance.pk and not self.cleaned_data.get(field_name):
                current_value = type(self.instance).objects.filter(pk=self.instance.pk).values_list(field_name, flat=True).first()
                setattr(self.instance, field_name, current_value or "")
        return super().save(commit=commit)


class OneCIntegrationSettingsForm(RetainedSecretModelForm):
    retained_secret_fields = ("password", "api_token")

    class Meta:
        model = OneCIntegrationSettings
        fields = (
            "enabled",
            "base_url",
            "username",
            "password",
            "api_token",
            "departments_endpoint",
            "employees_endpoint",
            "assets_endpoint",
            "verify_ssl",
            "timeout_seconds",
            "sync_departments",
            "sync_employees",
            "sync_assets",
        )
        widgets = {
            "enabled": forms.CheckboxInput(),
            "base_url": forms.URLInput(attrs={"class": "text-input", "placeholder": "https://1c.company.local/odata"}),
            "username": forms.TextInput(attrs={"class": "text-input", "placeholder": "svc_inventory"}),
            "password": forms.PasswordInput(attrs={"class": "text-input", "placeholder": "Оставьте пустым, чтобы не менять"}, render_value=False),
            "api_token": forms.PasswordInput(attrs={"class": "text-input", "placeholder": "Bearer token"}, render_value=False),
            "departments_endpoint": forms.TextInput(attrs={"class": "text-input"}),
            "employees_endpoint": forms.TextInput(attrs={"class": "text-input"}),
            "assets_endpoint": forms.TextInput(attrs={"class": "text-input"}),
            "verify_ssl": forms.CheckboxInput(),
            "timeout_seconds": forms.NumberInput(attrs={"class": "text-input", "min": "1"}),
            "sync_departments": forms.CheckboxInput(),
            "sync_employees": forms.CheckboxInput(),
            "sync_assets": forms.CheckboxInput(),
        }
        labels = {
            "enabled": "Интеграция активна",
            "base_url": "Базовый URL 1С",
            "username": "Логин API",
            "password": "Пароль API",
            "api_token": "API токен",
            "departments_endpoint": "Endpoint отделов",
            "employees_endpoint": "Endpoint сотрудников",
            "assets_endpoint": "Endpoint ТМЦ",
            "verify_ssl": "Проверять SSL сертификат",
            "timeout_seconds": "Таймаут, сек",
            "sync_departments": "Синхронизировать отделы",
            "sync_employees": "Синхронизировать сотрудников",
            "sync_assets": "Синхронизировать ТМЦ",
        }

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("enabled") and not cleaned_data.get("base_url"):
            self.add_error("base_url", "Укажите базовый URL 1С для активной интеграции.")
        return cleaned_data


class ActiveDirectorySettingsForm(RetainedSecretModelForm):
    retained_secret_fields = ("bind_password",)

    class Meta:
        model = ActiveDirectorySettings
        fields = (
            "enabled",
            "server_uri",
            "domain",
            "base_dn",
            "bind_dn",
            "bind_password",
            "user_search_filter",
            "email_attribute",
            "first_name_attribute",
            "last_name_attribute",
            "middle_name_attribute",
            "department_attribute",
            "title_attribute",
            "location_attribute",
            "display_name_attribute",
            "use_ssl",
            "timeout_seconds",
            "sync_profile_on_login",
        )
        widgets = {
            "enabled": forms.CheckboxInput(),
            "server_uri": forms.TextInput(attrs={"class": "text-input", "placeholder": "dc01.company.local"}),
            "domain": forms.TextInput(attrs={"class": "text-input", "placeholder": "COMPANY"}),
            "base_dn": forms.TextInput(attrs={"class": "text-input", "placeholder": "DC=company,DC=local"}),
            "bind_dn": forms.TextInput(attrs={"class": "text-input", "placeholder": "CN=svc_inventory,OU=Service Accounts,DC=company,DC=local"}),
            "bind_password": forms.PasswordInput(attrs={"class": "text-input", "placeholder": "Оставьте пустым, чтобы не менять"}, render_value=False),
            "user_search_filter": forms.TextInput(attrs={"class": "text-input"}),
            "email_attribute": forms.TextInput(attrs={"class": "text-input"}),
            "first_name_attribute": forms.TextInput(attrs={"class": "text-input"}),
            "last_name_attribute": forms.TextInput(attrs={"class": "text-input"}),
            "middle_name_attribute": forms.TextInput(attrs={"class": "text-input"}),
            "department_attribute": forms.TextInput(attrs={"class": "text-input"}),
            "title_attribute": forms.TextInput(attrs={"class": "text-input"}),
            "location_attribute": forms.TextInput(attrs={"class": "text-input"}),
            "display_name_attribute": forms.TextInput(attrs={"class": "text-input"}),
            "use_ssl": forms.CheckboxInput(),
            "timeout_seconds": forms.NumberInput(attrs={"class": "text-input", "min": "1"}),
            "sync_profile_on_login": forms.CheckboxInput(),
        }
        labels = {
            "enabled": "Интеграция активна",
            "server_uri": "Сервер LDAP/AD",
            "domain": "Домен",
            "base_dn": "Base DN",
            "bind_dn": "Учетная запись для поиска",
            "bind_password": "Пароль учетной записи",
            "user_search_filter": "LDAP фильтр поиска пользователя",
            "email_attribute": "Атрибут email",
            "first_name_attribute": "Атрибут имени",
            "last_name_attribute": "Атрибут фамилии",
            "middle_name_attribute": "Атрибут отчества",
            "department_attribute": "Атрибут отдела",
            "title_attribute": "Атрибут должности",
            "location_attribute": "Атрибут локации",
            "display_name_attribute": "Атрибут отображаемого имени",
            "use_ssl": "Использовать SSL",
            "timeout_seconds": "Таймаут, сек",
            "sync_profile_on_login": "Обновлять профиль сотрудника при входе",
        }

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("enabled"):
            for field_name in ("server_uri", "base_dn"):
                if not cleaned_data.get(field_name):
                    self.add_error(field_name, "Заполните это поле для активной интеграции.")
        return cleaned_data

