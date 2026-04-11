from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm

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
