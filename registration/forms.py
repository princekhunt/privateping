from django import forms
from django.contrib.auth.models import User
from chat.models import UserProfile
from django.core.validators import RegexValidator
from django.contrib.auth import password_validation

# Usernames end up in URLs, WebSocket group names, HTML ids and JS strings,
# so keep them to a safe character set.
username_validator = RegexValidator(
    r"^[A-Za-z0-9_]+$",
    "Username may contain only letters, digits and underscores.",
)

class SignUpForm(forms.Form):

    username = forms.CharField(min_length=5, max_length=20, validators=[username_validator])
    name = forms.CharField(max_length=25, label="Name", strip=True)
    email = forms.EmailField(label="Email")
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm Password", widget=forms.PasswordInput)

    def clean_name(self):
        name = self.cleaned_data["name"]
        if any(ord(ch) < 32 for ch in name):
            raise forms.ValidationError("Name contains invalid characters.")
        return name

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Username already taken.")
        return username

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password1") != cleaned.get("password2"):
            raise forms.ValidationError("Passwords do not match.")
        if cleaned.get("password1"):
            try:
                password_validation.validate_password(
                    cleaned["password1"], User(username=cleaned.get("username", "")))
            except forms.ValidationError as exc:
                self.add_error("password1", exc)
        return cleaned

    def save(self, commit=True):
        user = User.objects.create_user(
            self.cleaned_data['username'],
            self.cleaned_data['email'],
            self.cleaned_data['password1']
        )
        return user
