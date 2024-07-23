from django import forms
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.contrib.auth import password_validation


class CustomSetPasswordForm(SetPasswordForm):
    error_messages = {
        "password_mismatch": _("Nowe hasła nie są takie same."),
    }

    new_password1 = forms.CharField(
        label=_("New password"),
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )
    new_password2 = forms.CharField(
        label=_("New password confirmation"),
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    def clean_new_password2(self):
        password1 = self.cleaned_data.get("new_password1")
        password2 = self.cleaned_data.get("new_password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError(
                self.error_messages["password_mismatch"],
                code="password_mismatch",
            )
        password_validation.validate_password(password2, self.user)
        return password2

    def save(self, commit=True):
        password = self.cleaned_data["new_password1"]
        self.user.set_password(password)
        if commit:
            self.user.save()
        return self.user


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput,
        label="Hasło",
        help_text="Hasło musi zawierać co najmniej jedną cyfrę, jeden znak specjalny, jedną małą literę oraz jedną wielką literę.",
        error_messages={'required': 'To pole jest wymagane.'}
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput,
        label="Powtórz hasło",
        error_messages={'required': 'To pole jest wymagane.'}
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']
        error_messages = {
            'required': 'To pole jest wymagane.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set custom error messages for required fields
        self.fields['first_name'].required = True
        self.fields['first_name'].error_messages = {'required': 'To pole jest wymagane.'}

        self.fields['last_name'].required = True
        self.fields['last_name'].error_messages = {'required': 'To pole jest wymagane.'}

        self.fields['username'].error_messages = {'required': 'To pole jest wymagane.'}
        self.fields['email'].error_messages = {'required': 'To pole jest wymagane.'}

    def clean_password(self):
        password = self.cleaned_data.get('password')
        try:
            validate_password(password, user=None)  # Use Django's default password validators
        except ValidationError as e:
            raise ValidationError(e.messages, code='password_validation')
        return password

    def clean_password2(self):
        password1 = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise ValidationError("Hasła nie są zgodne!")
        return password2

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Użytkownik o podanym adresie email już istnieje!")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("Użytkownik o takiej nazwie już istnieje!")
        return username
