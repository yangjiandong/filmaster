from film20.core.models import Profile, User
from django.conf import settings

users_with_primary = set(p.user_id for p in Profile.all_profiles.filter(is_primary=True))
users_with_non_primary = set(p.user_id for p in Profile.all_profiles.filter(is_primary=False))

for p in Profile.all_profiles.filter(user__id__in=(users_with_non_primary - users_with_primary)):
  p.is_primary = True
  p.save()
  print p, 'changed to primary'

users_with_primary = set(p.user_id for p in Profile.all_profiles.filter(is_primary=True))
all_users = set(u.id for u in User.objects.all())

if all_users == users_with_primary:
    print 'all users have profiles'
    Profile.all_profiles.filter(is_primary=False).delete()
else:
    print 'creating missing profiles'
    for u in User.objects.filter(id__in=(all_users - users_with_primary)):
      print Profile.objects.create(user=u, LANG=settings.LANGUAGE_CODE)
