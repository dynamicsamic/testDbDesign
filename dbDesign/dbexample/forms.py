from django import forms
from django.contrib.auth import get_user_model


class UserRegistrationForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Enter password", widget=forms.PasswordInput
    )
    password2 = forms.CharField(
        label="Confirm password", widget=forms.PasswordInput
    )

    class Meta:
        model = get_user_model()
        fields = ("username", "email")

    def clean_password2(self):
        """Passwords must be identical."""
        data = self.cleaned_data
        if data.get("password1") != data.get("password2"):
            raise forms.ValidationError("Passwords don't match. Try again.")
        return data.get("password2")
