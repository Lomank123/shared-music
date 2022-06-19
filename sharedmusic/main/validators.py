from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
import re
from main import consts


class CustomPasswordSymbolValidator:
    """
    Validator to check whether password contains only A-Z, a-z, 0-9 or special symbols.
    """

    def validate(self, password, user=None):
        print(re.fullmatch(r'[A-Za-z0-9@$!%*#?&]+', password))
        if re.fullmatch(r'[A-Za-z0-9@$!%*#?&]+', password) is None:
            raise ValidationError(consts.SYMBOL_ERROR_MESSAGE, code='wrong_characters')

    def get_help_text(self):
        return _(consts.SYMBOL_ERROR_MESSAGE)
