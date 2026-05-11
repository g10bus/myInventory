from django import forms

from apps.accounts.models import User

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
                "required": True,
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

    def clean_image(self):
        image = self.cleaned_data.get("image")
        if not image:
            raise forms.ValidationError("Прикрепите фотофиксацию перед сохранением.")
        return image


class EmployeeInventoryAssignmentForm(forms.Form):
    employee = forms.ModelChoiceField(
        queryset=User.objects.none(),
        label="Сотрудник",
        widget=forms.Select(attrs={"class": "select-input", "id": "employee-select"}),
    )
    date_from = forms.DateField(
        label="Период с",
        widget=forms.DateInput(attrs={"class": "text-input", "type": "date"}),
    )
    date_to = forms.DateField(
        label="Период по",
        widget=forms.DateInput(attrs={"class": "text-input", "type": "date"}),
    )
    note = forms.CharField(
        required=False,
        label="Комментарий для сотрудника",
        widget=forms.Textarea(
            attrs={
                "class": "textarea-input",
                "rows": 4,
                "placeholder": "Например: нужно подтвердить фактическое наличие и актуальную локацию всех закрепленных ТМЦ.",
            }
        ),
    )

    def __init__(self, *args, employee_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        queryset = employee_queryset if employee_queryset is not None else User.objects.none()
        self.fields["employee"].queryset = queryset
        self.fields["employee"].label_from_instance = self.build_employee_label

    def build_employee_label(self, user):
        department_name = user.department.name if user.department else "Без отдела"
        return f"{user.full_name} • {user.email} • {department_name}"

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get("date_from")
        date_to = cleaned_data.get("date_to")

        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError("Дата окончания не может быть раньше даты начала.")

        return cleaned_data
