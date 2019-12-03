from django import forms

class AddressForm(forms.Form):
    ip = forms.GenericIPAddressField()
    port = forms.IntegerField()

