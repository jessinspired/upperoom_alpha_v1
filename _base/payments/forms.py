from django import forms
from .models import CreatorTransferInfo


class CreatorTransferInfoForm(forms.ModelForm):
    class Meta:
        model = CreatorTransferInfo
        fields = ['account_number', 'bank_code', 'bvn']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['account_number'].widget.attrs.update({'placeholder': 'Account Number'})
        self.fields['bank_code'].widget.attrs.update({'placeholder': 'Bank Code'})
        self.fields['bvn'].widget.attrs.update({'placeholder': 'Bank Verification Number'})