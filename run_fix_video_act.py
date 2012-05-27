import os
from copy import deepcopy


os.environ['DJANGO_SETTINGS_MODULE'] = 'film20.settings'
from django.db.models.query_utils import Q
from film20.externallink.models import *
from film20.useractivity.models import UserActivity
def fix_video_act():
    videos = ExternalLink.objects.filter(
                                    Q(url_kind__gt = ExternalLink.NEWS),
                                    Q(url_kind__lt= ExternalLink.BOOK),
                                    Q(status=ExternalLink.PUBLIC_STATUS)
                                    )
    for v in videos:
        if v.LANG == "pl":
            new_link = ExternalLink(
                url = v.url,
                url_kind = v.url_kind,
                video_thumb = v.video_thumb,
                film=v.film,
                user=v.user,
                permalink = 'LINK',
                version = 1,
                type = ExternalLink.TYPE_LINK,
                status = ExternalLink.PUBLIC_STATUS,
            )
            new_link.save(LANG="en")
            #act = UserActivity(user = v_copy.user, activity_type = UserActivity.TYPE_LINK, link = v_copy, created_at=v.created_at, LANG="en")
            try:
                act = UserActivity.objects.get(link=v_copy, link__status=ExternalLink.PUBLIC_STATUS)
                act.created_at = v.created_at
                act.save()
            except :
                pass
        elif v.LANG == "en":
            new_link = ExternalLink(
                url = v.url,
                url_kind = v.url_kind,
                video_thumb = v.video_thumb,
                film=v.film,
                user=v.user,
                permalink = 'LINK',
                version = 1,
                type = ExternalLink.TYPE_LINK,
                status = ExternalLink.PUBLIC_STATUS,
            )
            new_link.save()
            #act = UserActivity(user = v_copy.user, activity_type = UserActivity.TYPE_LINK, link = v_copy,created_at=v.created_at, LANG="pl")
            try:
                act = UserActivity.objects.get(link=v_copy, link__status=ExternalLink.PUBLIC_STATUS)
                act.created_at = v.created_at
                act.save()
            except :
                pass
def main():
    fix_video_act()

if __name__ == "__main__":
    fix_video_act()
  