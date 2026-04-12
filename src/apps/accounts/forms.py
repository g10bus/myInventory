from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm

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
            field.widget.attrs.update(
                {
                    "class": "text-input",
                }
            )


class UserAdminManageForm(forms.ModelForm):
    remove_avatar = forms.BooleanField(required=False, label="Удалить текущий аватар")

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
            "is_active",
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
            "is_active": "Активный пользователь",
            "is_staff": "Доступ к staff-функциям",
            "is_superuser": "Полный доступ суперпользователя",
        }

    def __init__(self, *args, actor=None, **kwargs):
        self.actor = actor
        super().__init__(*args, **kwargs)
        self.fields["avatar"].required = False

        if not actor or not actor.is_superuser:
            self.fields.pop("is_staff", None)
            self.fields.pop("is_superuser", None)

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

        self.instance.email = self.cleaned_data["email"].lower()
        self.instance.username = self.instance.email
        return super().save(commit=commit)
