from decimal import Decimal
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
        
        
class PaymentRequestForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.01'),
        error_messages={
            'required': 'Amount is required.',
            'min_value': 'The amount must be at least N0.01.',
        },
        widget=forms.NumberInput(attrs={
            'placeholder': 'Enter amount',
            'class': 'form-control'
        })
    )