from django import forms

from staff.models import Staff
from staff.choices import ROLE_CHOICES, PERMISSION_CHOICES
from stores.models import Store


PERMISSION_CHOICE_TUPLES = [(p[0], p[1]) for p in PERMISSION_CHOICES]


class StaffCreateForm(forms.Form):
    store = forms.ModelChoiceField(
        queryset=Store.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Store",
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "staff@example.com"}),
        label="Email",
    )
    first_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "First name"}),
        label="First name",
    )
    last_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Last name"}),
        label="Last name",
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "••••••••"}),
        label="Password",
    )
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Role",
    )
    permissions = forms.MultipleChoiceField(
        choices=PERMISSION_CHOICE_TUPLES,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
        label="Custom permissions (optional)",
        help_text="Leave empty to use role defaults. Override to fine-tune access.",
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields["store"].queryset = Store.objects.filter(owner=user).order_by(
                "name"
            )
        else:
            self.fields["store"].queryset = Store.objects.none()


class StaffUpdateForm(forms.ModelForm):
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    permissions = forms.MultipleChoiceField(
        choices=PERMISSION_CHOICE_TUPLES,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
        label="Custom permissions",
        help_text="Leave empty to use role defaults.",
    )

    class Meta:
        model = Staff
        fields = ["role"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.initial["permissions"] = self.instance.permissions or []

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.permissions = self.cleaned_data.get("permissions", []) or []
        if commit:
            instance.save()
        return instance
