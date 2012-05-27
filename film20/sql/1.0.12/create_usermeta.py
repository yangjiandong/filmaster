import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'film20.settings'
from film20.core.models import *

total = User.objects.count()
cnt = 0

for user in User.objects.all():
    meta = UserMeta.get(user, recommendations_notice_sent=True)
    print "%s/%s" % (cnt, total)
    cnt+=1
    