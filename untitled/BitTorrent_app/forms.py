from django import forms

class AddressForm(forms.Form):
    ip = forms.GenericIPAddressField()
    port = forms.IntegerField()

    dht_ip = forms.GenericIPAddressField()
    dht_port = forms.IntegerField()

class UploadFileForm(forms.Form):
    uploaded_file = forms.FileField()
