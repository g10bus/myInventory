from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm
from django.contrib.auth.models import Group

from apps.org.models import Location

from .models import User


def split_full_name(full_name):
    parts = [part for part in full_name.split() if part]
    last_name = parts[0].capitalize() if len(parts) > 0 else ""
    first_name = parts[1].capitalize() if len(parts) > 1 else ""
    middle_name = parts[2].capitalize() if len(parts) > 2 else ""
    return last_name, first_name, middle_name


class LoginForm(forms.Form):
    email = forms.EmailField(label="Email")
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")
        if email and password:
            existing_user = User.objects.filter(email__iexact=email).first()
            if existing_user and existing_user.check_password(password) and not existing_user.is_active:
                raise forms.ValidationError("Ваш аккаунт заблокирован. Вход в систему недоступен.")
            self.user = authenticate(email=email, password=password)
            if self.user is None:
                raise forms.ValidationError("Неверная почта или пароль.")
        return cleaned_data

    def get_user(self):
        return getattr(self, "user", None)


class RegistrationForm(UserCreationForm):
    full_name = forms.CharField(label="ФИО")

    class Meta:
        model = User
        fields = ("email", "full_name", "phone", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Пользователь с такой почтой уже существует.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        last_name, first_name, middle_name = split_full_name(self.cleaned_data["full_name"])
        user.email = self.cleaned_data["email"].lower()
        user.username = user.email
        user.last_name = last_name
        user.first_name = first_name
        user.middle_name = middle_name
        user.phone = self.cleaned_data["phone"]
        if commit:
            user.save()
        return user


class ProfileSettingsForm(forms.ModelForm):
    remove_avatar = forms.BooleanField(required=False, label="Удалить текущий аватар")

    class Meta:
        model = User
        fields = ("email", "avatar")
        widgets = {
            "email": forms.EmailInput(
                attrs={
                    "class": "text-input",
                    "placeholder": "employee@company.ru",
                }
            ),
            "avatar": forms.FileInput(
                attrs={
                    "class": "file-input",
                    "accept": "image/*",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["avatar"].required = False

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Пользователь с такой почтой уже существует.")
        return email

    def save(self, commit=True):
        existing_avatar = None
        if self.instance.pk:
            existing_avatar = type(self.instance).objects.get(pk=self.instance.pk).avatar

        remove_avatar = self.cleaned_data.get("remove_avatar")
        new_avatar = self.cleaned_data.get("avatar")

        if remove_avatar and existing_avatar:
            existing_avatar.delete(save=False)
            self.instance.avatar = None
        elif new_avatar and existing_avatar and existing_avatar.name != new_avatar.name:
            existing_avatar.delete(save=False)

        self.instance.email = self.cleaned_data["email"]
        self.instance.username = self.cleaned_data["email"]
        return super().save(commit=commit)


class StyledPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({"class": "text-input"})


class AdminModeConfirmationForm(forms.Form):
    password = forms.CharField(
        label="Текущий пароль",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "text-input",
                "autocomplete": "current-password",
                "placeholder": "Введите текущий пароль",
            }
        ),
    )

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_password(self):
        password = self.cleaned_data["password"]
        if not self.user or not self.user.check_password(password):
            raise forms.ValidationError("Указан неверный пароль.")
        return password


class UserAdminManageForm(forms.ModelForm):
    remove_avatar = forms.BooleanField(required=False, label="Удалить текущий аватар")
    blocked_user = forms.BooleanField(required=False, label="Заблокировать пользователя")
    administrator_access = forms.BooleanField(
        required=False,
        label="Админ-доступ",
        help_text="Даёт доступ к админ-режиму и административным разделам.",
    )

    class Meta:
        model = User
        fields = (
            "email",
            "avatar",
            "last_name",
            "first_name",
            "middle_name",
            "phone",
            "role",
            "position",
            "office_location",
            "department",
            "is_staff",
            "is_superuser",
        )
        widgets = {
            "email": forms.EmailInput(attrs={"class": "text-input"}),
            "avatar": forms.FileInput(attrs={"class": "text-input", "accept": "image/*"}),
            "last_name": forms.TextInput(attrs={"class": "text-input"}),
            "first_name": forms.TextInput(attrs={"class": "text-input"}),
            "middle_name": forms.TextInput(attrs={"class": "text-input"}),
            "phone": forms.TextInput(attrs={"class": "text-input"}),
            "role": forms.TextInput(attrs={"class": "text-input"}),
            "position": forms.TextInput(attrs={"class": "text-input"}),
            "office_location": forms.TextInput(attrs={"class": "text-input"}),
            "department": forms.Select(attrs={"class": "select-input"}),
        }
        labels = {
            "email": "Email",
            "avatar": "Аватар",
            "last_name": "Фамилия",
            "first_name": "Имя",
            "middle_name": "Отчество",
            "phone": "Телефон",
            "role": "Роль",
            "position": "Должность",
            "office_location": "Локация",
            "department": "Отдел",
            "is_staff": "Доступ к staff-функциям",
            "is_superuser": "Полный доступ суперпользователя",
        }

    def __init__(self, *args, actor=None, **kwargs):
        self.actor = actor
        super().__init__(*args, **kwargs)
        self.fields["avatar"].required = False
        self.fields["blocked_user"].initial = not self.instance.is_active
        self.fields["administrator_access"].initial = self.instance.is_administrator
        self.fields["department"].queryset = self.fields["department"].queryset.order_by("name")

        location_choices = [("", "Не указана")]
        location_choices.extend([(location.name, location.name) for location in Location.objects.order_by("name")])
        current_location = (self.instance.office_location or "").strip()
        if current_location and current_location not in {value for value, _ in location_choices}:
            location_choices.append((current_location, current_location))
        self.fields["office_location"] = forms.ChoiceField(
            required=False,
            label="Локация",
            choices=location_choices,
            widget=forms.Select(attrs={"class": "select-input"}),
        )
        self.initial["office_location"] = current_location

        if not actor or not actor.is_superuser:
            self.fields.pop("is_staff", None)
            self.fields.pop("is_superuser", None)
        else:
            self.fields.pop("is_staff", None)

        if not actor or not self.instance.pk or actor.pk == self.instance.pk:
            self.fields.pop("administrator_access", None)

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Пользователь с такой почтой уже существует.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        if (
            "administrator_access" in self.fields
            and self.actor
            and self.instance.pk
            and self.actor.pk == self.instance.pk
        ):
            raise forms.ValidationError("Нельзя менять собственный админ-доступ через эту форму.")
        return cleaned_data

    def save(self, commit=True):
        existing_avatar = None
        if self.instance.pk:
            existing_avatar = type(self.instance).objects.get(pk=self.instance.pk).avatar

        remove_avatar = self.cleaned_data.get("remove_avatar")
        new_avatar = self.cleaned_data.get("avatar")

        if remove_avatar and existing_avatar:
            existing_avatar.delete(save=False)
            self.instance.avatar = None
        elif new_avatar and existing_avatar and existing_avatar.name != new_avatar.name:
            existing_avatar.delete(save=False)

        self.instance.email = self.cleaned_data["email"].lower()
        self.instance.username = self.instance.email
        self.instance.is_active = not self.cleaned_data.get("blocked_user", False)
        instance = super().save(commit=commit)

        if "administrator_access" in self.fields and instance.pk:
            admin_group, _ = Group.objects.get_or_create(name="system_admin")
            operator_group, _ = Group.objects.get_or_create(name="inventory_operator")
            should_have_admin_access = self.cleaned_data.get("administrator_access", False)

            if should_have_admin_access:
                instance.groups.add(admin_group)
            else:
                instance.groups.remove(admin_group, operator_group)
                if not instance.is_superuser and instance.is_staff:
                    instance.is_staff = False
                    instance.save(update_fields=["is_staff"])

        return instance
