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
