from django import template

import logging
logger = logging.getLogger(__name__)

register = template.Library()

@register.filter(name="dir")
def _dir(value):
	keys = getattr(value, "keys", None)
	if callable(keys):
		keys = keys()
	else:
		keys = dir(value)
	return repr([k for k in keys if not k.startswith("_")])
