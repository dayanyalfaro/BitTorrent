from django import forms
from BitTorrent_app.models import UploadedFile

class AddressForm(forms.Form):
    ip = forms.GenericIPAddressField()
    port = forms.IntegerField()


class UploadFileForm(forms.ModelForm):
    class Meta:
        model = UploadedFile
        fields = ['uploaded_file',]
