from film20.useractivity.models import UserActivity

query = UserActivity.objects.all().exclude(activity_type=UserActivity.TYPE_COMMENT)

total = query.count()
for i, ua in enumerate(query):
    print i+1, "/", total
    ua.update_tags(UserActivity, ua, False)

