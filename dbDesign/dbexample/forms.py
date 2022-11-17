from django import forms

from . import models


class UserRegistrationForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Enter password", widget=forms.PasswordInput
    )
    password2 = forms.CharField(
        label="Confirm password", widget=forms.PasswordInput
    )

    class Meta:
        model = models.User
        fields = ("username", "email")

    def clean_password2(self):
        """Passwords must be identical."""
        data = self.cleaned_data
        if data.get("password1") != data.get("password2"):
            raise forms.ValidationError("Passwords don't match. Try again.")
        return data.get("password2")
