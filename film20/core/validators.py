from django.core.validators import RegexValidator
from django.utils.translation import ugettext_lazy as _

validate_login = RegexValidator(r'^[a-zA-Z0-9-]+$', _("Enter valid username"))
