#!/bin/bash
django-admin.py makemessages -l en --extension=html,txt
django-admin.py makemessages -l pl --extension=html,txt
django-admin.py makemessages -d djangojs -l pl
django-admin.py makemessages -d djangojs -l en

# vim locale/pl/LC_MESSAGES/django.po
# vim locale/en/LC_MESSAGES/django.po
# vim locale/pl/LC_MESSAGES/djangojs.po
# vim locale/en/LC_MESSAGES/djangojs.po

django-admin.py compilemessages
