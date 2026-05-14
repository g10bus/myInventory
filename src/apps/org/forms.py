from django import forms

from .models import Department, Location


class LocationCreateForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ("name", "code", "address")
        labels = {
            "name": "Название локации",
            "code": "Код",
            "address": "Адрес или описание",
        }
        widgets = {
            "name": forms.TextInput(attrs={"class": "text-input", "placeholder": "Например: Офис 1"}),
            "code": forms.TextInput(attrs={"class": "text-input", "placeholder": "Например: OFC-1"}),
            "address": forms.TextInput(
                attrs={"class": "text-input", "placeholder": "Например: Москва, 3 этаж, кабинет 305"}
            ),
        }


class DepartmentCreateForm(forms.ModelForm):
    location_name = forms.ModelChoiceField(
        queryset=Location.objects.none(),
        required=False,
        label="Базовая локация",
        empty_label="Без привязки к локации",
        widget=forms.Select(attrs={"class": "select-input"}),
    )

    class Meta:
        model = Department
        fields = ("name", "code")
        labels = {
            "name": "Название отдела",
            "code": "Код",
        }
        widgets = {
            "name": forms.TextInput(attrs={"class": "text-input", "placeholder": "Например: IT отдел"}),
            "code": forms.TextInput(attrs={"class": "text-input", "placeholder": "Например: IT"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["location_name"].queryset = Location.objects.order_by("name")

    def save(self, commit=True):
        instance = super().save(commit=False)
        selected_location = self.cleaned_data.get("location_name")
        instance.location = selected_location.name if selected_location else ""
        if commit:
            instance.save()
        return instance
