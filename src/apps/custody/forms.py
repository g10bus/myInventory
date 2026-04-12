from django import forms
from django.contrib.auth import get_user_model

from apps.custody.models import AssetAssignment
from apps.inventory.models import Asset

User = get_user_model()


def _apply_text_style(field):
    widget = field.widget
    css_class = "text-input"
    if isinstance(widget, forms.Select):
        css_class = "select-input"
    elif isinstance(widget, forms.Textarea):
        css_class = "textarea-input"
    widget.attrs.setdefault("class", css_class)


class TransferRequestForm(forms.Form):
    asset_id = forms.ModelChoiceField(
        queryset=Asset.objects.none(),
        label="ТМЦ",
    )
    recipient_id = forms.ModelChoiceField(
        queryset=User.objects.none(),
        label="Получатель",
    )
    comment = forms.CharField(
        label="Комментарий",
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
    )

    def __init__(self, *args, asset_queryset=None, recipient_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["asset_id"].queryset = asset_queryset or Asset.objects.none()
        self.fields["recipient_id"].queryset = recipient_queryset or User.objects.none()
        for field in self.fields.values():
            _apply_text_style(field)


class AssetIssueForm(forms.Form):
    asset = forms.ModelChoiceField(
        queryset=Asset.objects.none(),
        label="ТМЦ",
    )
    employee = forms.ModelChoiceField(
        queryset=User.objects.none(),
        label="Сотрудник",
    )
    note = forms.CharField(
        label="Комментарий к выдаче",
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
    )

    def __init__(self, *args, asset_queryset=None, employee_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["asset"].queryset = asset_queryset or Asset.objects.none()
        self.fields["employee"].queryset = employee_queryset or User.objects.none()
        for field in self.fields.values():
            _apply_text_style(field)


class AssetReturnForm(forms.Form):
    assignment = forms.ModelChoiceField(
        queryset=AssetAssignment.objects.none(),
        label="Активное закрепление",
    )
    location = forms.CharField(
        label="Локация после возврата",
        initial="Склад",
    )
    note = forms.CharField(
        label="Комментарий к возврату",
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
    )

    def __init__(self, *args, assignment_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assignment"].queryset = assignment_queryset or AssetAssignment.objects.none()
        self.fields["assignment"].label_from_instance = (
            lambda assignment: (
                f"{assignment.asset.title} • {assignment.asset.inventory_number} • "
                f"{assignment.employee.short_name}"
            )
        )
        for field in self.fields.values():
            _apply_text_style(field)


class AdminTransferRequestForm(forms.Form):
    asset = forms.ModelChoiceField(
        queryset=Asset.objects.none(),
        label="ТМЦ",
    )
    recipient = forms.ModelChoiceField(
        queryset=User.objects.none(),
        label="Получатель",
    )
    comment = forms.CharField(
        label="Комментарий к передаче",
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
    )

    def __init__(self, *args, asset_queryset=None, recipient_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["asset"].queryset = asset_queryset or Asset.objects.none()
        self.fields["recipient"].queryset = recipient_queryset or User.objects.none()
        for field in self.fields.values():
            _apply_text_style(field)

    def clean(self):
        cleaned_data = super().clean()
        asset = cleaned_data.get("asset")
        recipient = cleaned_data.get("recipient")

        if not asset or not recipient:
            return cleaned_data

        current_assignment = asset.assignments.filter(is_current=True).select_related("employee").first()
        if current_assignment is None:
            raise forms.ValidationError("Нельзя оформить передачу: ТМЦ сейчас не закреплено за сотрудником.")

        if current_assignment.employee_id == recipient.pk:
            raise forms.ValidationError("Получатель уже является текущим ответственным за это ТМЦ.")

        cleaned_data["current_assignment"] = current_assignment
        return cleaned_data
