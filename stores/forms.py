from django import forms

from .models import Store


class StoreForm(forms.ModelForm):
    class Meta:
        model = Store
        fields = [
            "name",
            "description",
            "sheet_webhook",
            "site",
            "FB_PAGE",
            "INSTA_PAGE",
            "PHONE_NUMBER",
            "EMAIL",
            "WHATSAPP",
            "THEME_COLOR",
            "LOGO",
            "FAKE_PIXEL",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }
