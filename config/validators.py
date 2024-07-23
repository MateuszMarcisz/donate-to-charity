import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from django.contrib.auth.password_validation import (
    UserAttributeSimilarityValidator,
    MinimumLengthValidator,
    CommonPasswordValidator,
    NumericPasswordValidator
)
from difflib import SequenceMatcher


class CustomUserAttributeSimilarityValidator(UserAttributeSimilarityValidator):
    def _is_value_too_similar(self, value, password):
        return SequenceMatcher(a=value.lower(), b=password.lower()).quick_ratio() >= 0.7

    def validate(self, password, user=None):
        if user:
            password_data = [
                (user.username, _("Twoje hasło nie może być zbyt podobne do twojej nazwy użytkownika.")),
                (user.first_name, _("Twoje hasło nie może być zbyt podobne do twojego imienia.")),
                (user.last_name, _("Twoje hasło nie może być zbyt podobne do twojego nazwiska.")),
                (user.email, _("Twoje hasło nie może być zbyt podobne do twojego adresu e-mail."))
            ]
            for value, error_message in password_data:
                if value and self._is_value_too_similar(value, password):
                    raise ValidationError(
                        error_message,
                        code='password_too_similar',
                    )


class CustomMinimumLengthValidator(MinimumLengthValidator):
    def validate(self, password, user=None):
        if len(password) < self.min_length:
            raise ValidationError(
                _("Twoje hasło musi zawierać przynajmniej %(min_length)d znaków.") % {'min_length': self.min_length},
                code='password_too_short',
            )


class CustomCommonPasswordValidator(CommonPasswordValidator):
    def validate(self, password, user=None):
        if password.lower() in self.passwords:
            raise ValidationError(
                _("Twoje hasło jest zbyt powszechne."),
                code='password_too_common',
            )


class CustomNumericPasswordValidator(NumericPasswordValidator):
    def validate(self, password, user=None):
        if password.isdigit():
            raise ValidationError(
                _("Twoje hasło nie może składać się wyłącznie z cyfr."),
                code='password_entirely_numeric',
            )


class CustomPasswordValidator:
    """
    Validator for checking password strength with additional requirements:
    - At least one digit
    - At least one special character
    - At least one uppercase and one lowercase letter
    """

    def validate(self, password, user=None):
        if not re.search(r'\d', password):
            raise ValidationError(
                _("Hasło musi zawierać co najmniej jedną cyfrę."),
                code='password_no_digit',
            )
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError(
                _("Hasło musi zawierać co najmniej jeden znak specjalny."),
                code='password_no_special',
            )
        if not re.search(r'[a-z]', password):
            raise ValidationError(
                _("Hasło musi zawierać co najmniej jedną małą literę."),
                code='password_no_lowercase',
            )
        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                _("Hasło musi zawierać co najmniej jedną wielką literę."),
                code='password_no_uppercase',
            )

    def get_help_text(self):
        return _(
            "Twoje hasło musi zawierać co najmniej jedną cyfrę, "
            "jeden znak specjalny, jedną małą literę oraz jedną wielką literę."
        )
