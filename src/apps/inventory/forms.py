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


class InventoryVerificationCreateForm(forms.Form):
    next_verification_date = forms.DateField(
        required=False,
        label="Следующая сверка",
        widget=forms.DateInput(attrs={"class": "text-input", "type": "date"}),
    )
    location = forms.CharField(
        required=False,
        label="Локация фиксации",
        widget=forms.TextInput(
            attrs={
                "class": "text-input",
                "placeholder": "Например: кабинет 305 или склад",
            }
        ),
    )
    note = forms.CharField(
        required=False,
        label="Комментарий к сверке",
        widget=forms.Textarea(
            attrs={
                "class": "textarea-input",
                "rows": 5,
                "placeholder": "Что проверили, в каком состоянии ТМЦ и есть ли замечания.",
            }
        ),
    )
    image = forms.ImageField(
        required=False,
        label="Фотофиксация",
        widget=forms.ClearableFileInput(
            attrs={
                "class": "file-input",
                "accept": "image/*",
            }
        ),
    )
    image_caption = forms.CharField(
        required=False,
        label="Подпись к фото",
        widget=forms.TextInput(
            attrs={
                "class": "text-input",
                "placeholder": "Например: общий вид рабочего места",
            }
        ),
    )
