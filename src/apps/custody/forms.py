from django import forms
from django.contrib.auth import get_user_model

from apps.inventory.models import Asset

User = get_user_model()


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
        self.fields["recipient_id"].queryset = recipient_queryset
