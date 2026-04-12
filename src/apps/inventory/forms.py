from django import forms

from .models import Asset


class AssetAdminForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = (
            "category",
            "title",
            "model_name",
            "inventory_number",
            "serial_number",
            "status",
            "location",
            "last_verified_at",
            "next_verification_date",
            "notes",
        )
        labels = {
            "category": "Категория",
            "title": "Наименование",
            "model_name": "Модель",
            "inventory_number": "Инвентарный номер",
            "serial_number": "Серийный номер",
            "status": "Статус",
            "location": "Локация",
            "last_verified_at": "Последняя сверка",
            "next_verification_date": "Следующая сверка",
            "notes": "Примечание",
        }
        widgets = {
            "category": forms.TextInput(attrs={"class": "text-input"}),
            "title": forms.TextInput(attrs={"class": "text-input"}),
            "model_name": forms.TextInput(attrs={"class": "text-input"}),
            "inventory_number": forms.TextInput(attrs={"class": "text-input"}),
            "serial_number": forms.TextInput(attrs={"class": "text-input"}),
            "status": forms.Select(attrs={"class": "select-input"}),
            "location": forms.TextInput(attrs={"class": "text-input"}),
            "last_verified_at": forms.DateInput(attrs={"class": "text-input", "type": "date"}),
            "next_verification_date": forms.DateInput(attrs={"class": "text-input", "type": "date"}),
            "notes": forms.Textarea(attrs={"class": "textarea-input", "rows": 5}),
        }
