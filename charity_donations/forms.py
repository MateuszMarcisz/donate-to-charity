from django import forms
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.contrib.auth import password_validation

from config.validators import CustomMinimumLengthValidator, CustomCommonPasswordValidator, \
    CustomNumericPasswordValidator, CustomPasswordValidator


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

        self.fields['email'].required = True
        self.fields['email'].error_messages = {'required': 'To pole jest wymagane.'}

    def clean_password(self):
        password = self.cleaned_data.get('password')
        try:
            validate_password(password, user=None)
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


class PasswordChangeForm(forms.Form):
    change_password = forms.CharField(
        widget=forms.PasswordInput,
        label='Nowe hasło',
        # min_length=8
    )
    change_password2 = forms.CharField(
        widget=forms.PasswordInput,
        label='Potwierdź nowe hasło'
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput,
        label='Obecne hasło'
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_change_password(self):
        password = self.cleaned_data.get('change_password')
        validate_password(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('change_password')
        password2 = cleaned_data.get('change_password2')
        confirm_password = cleaned_data.get('confirm_password')

        if password and password2 and password != password2:
            self.add_error('change_password2', 'Nowe hasła nie są zgodne.')

        if self.user and confirm_password and not self.user.check_password(confirm_password):
            self.add_error('confirm_password', 'Nieprawidłowe hasło użytkownika!')


class UserUpdateForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput,
        label="Podaj hasło, aby uwierzytelnić zmiany",
        error_messages={'required': 'To pole jest wymagane.'}
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        error_messages = {
            'username': {'required': 'To pole jest wymagane.'},
            'email': {'required': 'To pole jest wymagane.'},
            'first_name': {'required': 'To pole jest wymagane.'},
            'last_name': {'required': 'To pole jest wymagane.'}
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Użytkownik o takiej nazwie już istnieje!")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Użytkownik o podanym adresie email już istnieje!")
        return email

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not self.user.check_password(password):
            raise ValidationError("Nieprawidłowe hasło użytkownika!")
        return password


class ContactForm(forms.Form):
    name = forms.CharField(max_length=100, required=True)
    surname = forms.CharField(max_length=100, required=True)
    message = forms.CharField(widget=forms.Textarea, required=True)
