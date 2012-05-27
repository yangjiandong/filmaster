import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'film20.settings'
import sys
sys.path.insert(0, os.path.abspath('..'))
print sys.path[0]

from film20.messages.models import Message
Message.fix_all()
