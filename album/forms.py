from django import forms
from .models import Photo

class PhotoUploadForm(forms.ModelForm):
    class Meta:
        model = Photo
        fields = ["name", "image"]
        widgets = {
            "name": forms.TextInput(attrs={"maxlength": 40}),
        }