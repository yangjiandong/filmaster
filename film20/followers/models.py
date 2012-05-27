import django
from django.db import models, connection
from django.db.models.fields.related import create_many_related_manager, ManyToManyRel
from django.db import models
from django.conf import settings
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User
from film20.notification import models as notification
from film20.core.templatetags.map_url import url_username_link
from film20.utils.cache_helper import *
from film20.core.models import RatingComparator, TemporaryUser

import logging
logger = logging.getLogger(__name__)

LANGUAGE_CODE = settings.LANGUAGE_CODE

FOLLOW_TXT = _(' started following ')
if LANGUAGE_CODE == 'pl':
    FOLLOW_TXT = ' obserwuje co pisze '

class Followers(models.Model):

    FOLLOWING = 1
    UNKNOWN = 0
    BLOCKING = -1

    FOLLOW_STATUSES = (
        (FOLLOWING, _('Following')),
        (BLOCKING, _('Blocking')),
        (UNKNOWN, _('Unknown')),
    )

    from_user = models.ForeignKey(User, related_name='from_users')
    to_user = models.ForeignKey(User, related_name='to_users')
    status = models.IntegerField(default=FOLLOWING, choices=FOLLOW_STATUSES)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (('from_user', 'to_user', 'status'),)
        ordering = ('-created_at',)

    def __unicode__(self):
        return 'Relation from %s to %s' % (self.from_user.username, self.to_user.username)

    def save(self, *args, **kw):
        logger.debug("saving")
        first_save = False
        if self.pk is None:
            first_save = True
        super(Followers, self).save(*args, **kw)

        #                                                  v hack for #FLM-1572
        if first_save and self.status==Followers.FOLLOWING and self.to_user.username <> 'blog':
            self.save_activity()

            notification.send([self.to_user], "following",
                {
                    'to_user': self.to_user,
                    'from_user' : self.from_user,
                    'link' : url_username_link(self.from_user)
                }
            )

    def save_activity(self):
        """
            Save new activity. There is no need to update it
        """
        from film20.useractivity.models import UserActivity
        txt = self.from_user.username + " started_to_follow " + self.to_user.username
        act = UserActivity(user=self.from_user, LANG="pl", content=txt, username=self.from_user.username, activity_type=UserActivity.TYPE_FOLLOW)
        act.save()

        act = UserActivity(user=self.from_user, LANG="en", content=txt, username=self.from_user.username, activity_type=UserActivity.TYPE_FOLLOW)
        act.save()
        
field = models.ManyToManyField(User, through=Followers,
                               symmetrical=False, related_name='related_to')

class FollowingManager(User._default_manager.__class__):
    """
       Idea taken from this app:
       http://github.com/coleifer/django-relationships/tree/master/relationships/
    """

    def __init__(self, instance=None, *args, **kwargs):
        super(FollowingManager, self).__init__(*args, **kwargs)
        self.instance = instance

    def change_status(self, user, status):
        following, created = Followers.objects.get_or_create(
            from_user = self.instance,
            to_user = user,
            defaults = {
                'status':status
            }
        )
        if not created:
            following.status = status
            following.save()
 
        key = "%s_FOLLOWING" % self.instance.username
        delete_cache(CACHE_FOLLOWERS, key)
        key = "%s_FOLLOWERS" % user.username
        delete_cache(CACHE_FOLLOWERS, key)
        delete_cache(CACHE_FOLLOWERS, "%s_FRIENDS" % self.instance.username)
        delete_cache(CACHE_FOLLOWERS, "%s_FRIENDS" % user.username)
        return following

    def follow(self, user):
        """
           Add user to followers list, if user is add or relation
           aleready exists returns relation
        """
        return self.change_status(user, Followers.FOLLOWING)

    def remove(self, user):
        """
           Removes user from following list, if relation exists returns it
           if not returns None
           "I don't follow this user from now"
        """
        return self.change_status(user, Followers.UNKNOWN)

    def block(self, user):
        """
           Block user
           "I don't want to see his reviews"
        """
        return self.change_status(user, Followers.BLOCKING)

    def following(self):
        """
           Return following list for user
           "users that I follow"
        """
        key = "%s_FOLLOWING" % self.instance.username
        query = get_cache(CACHE_FOLLOWERS, key)
        if query is None:
            query = User.objects.filter(
                is_active=True,
                to_users__from_user=self.instance,
                to_users__status=Followers.FOLLOWING
            ).order_by( '-to_users__created_at' )
            set_cache(CACHE_FOLLOWERS, key, query)
        return query

    def followers(self):
        """
           Return followers list for user
           "users that follow me"
        """
        key = "%s_FOLLOWERS" % self.instance.username
        query = get_cache(CACHE_FOLLOWERS, key)
        if query is None:
            query = User.objects.filter(
                is_active=True,
                from_users__to_user=self.instance,
                from_users__status=Followers.FOLLOWING
            ).order_by( '-from_users__created_at' )
            set_cache(CACHE_FOLLOWERS, key, query)
        return query


    def blocking(self):
        """
           Return blocking list for user
           "users that i block"
        """
        key ="%s_BLOCKING" % self.instance.username
        query = get_cache(CACHE_FOLLOWERS, key)
        if query is None:
            query = User.objects.filter(
                is_active=True,
                to_users__from_user=self.instance,
                to_users__status=Followers.BLOCKING,)
            set_cache(CACHE_FOLLOWERS, key, query)
            return query
        else:
            return query

    def blockers(self):
        """
           Return blockers list for user
           "users that block Me"
        """
        key = "%s_BLOCKERS" % self.instance.username
        query = get_cache(CACHE_FOLLOWERS, key)
        if query is None:
            query = User.objects.filter(
                is_active=True,
                from_users__to_user=self.instance,
                from_users__status=Followers.BLOCKING,)
            set_cache(CACHE_FOLLOWERS, key, query)
            return query
        else:
            return query

    def friends(self):
        """
           Return friends
           "users that are following each other"
        """
        key = "%s_FRIENDS" % self.instance.username
        result = get_cache(CACHE_FOLLOWERS, key)
        if result is None:
            result = list(User.objects.filter(
                is_active=True,
                to_users__status=Followers.FOLLOWING,
                to_users__from_user=self.instance,
                from_users__status=Followers.FOLLOWING,
                from_users__to_user=self.instance,))
            set_cache(CACHE_FOLLOWERS, key, result)
        return result

    def similar_users(self, number):
        key = Key('similar_users_list', self.instance.username)
        users = get(key)
        if not users:
            users = []
            similar_users_list = RatingComparator.objects.filter(main_user=self.instance, score__lte=settings.SIMILAR_USER_LEVEL).select_related('user')[:number]
            if similar_users_list:
                for similar_user in similar_users_list:
                    users.append(similar_user.compared_user)
            set(key, users)
        return users

    def get_relation(self, user):
        """
           Return relation between users if there is not relation returns false
        """
        try:
            following = Followers.objects.get(
                            from_user = self.instance,
                            to_user = user,
                            )
            return following
        except Followers.DoesNotExist:
            return False

if django.VERSION < (1, 2):

    RelatedManager = create_many_related_manager(FollowingManager, Followers)

    class FollowersDescriptor(object):
        def __get__(self, instance, instance_type=None):
            qn = connection.ops.quote_name
            manager = RelatedManager(
                model=User,
                core_filters={'related_to__pk': instance._get_pk_val()},
                instance=instance,
                symmetrical=False,
                join_table=qn('followers_followers'),
                source_col_name=qn('from_user_id'),
                target_col_name=qn('to_user_id'),
            )
            return manager

else:

    fake_rel = ManyToManyRel(
        to=User,
        through=Followers)

    RelatedManager = create_many_related_manager(FollowingManager, fake_rel)

    class FollowersDescriptor(object):
        def __get__(self, instance, instance_type=None):
            manager = RelatedManager(
                model=User,
                core_filters={'related_to__pk': instance._get_pk_val()},
                instance=instance,
                symmetrical=False,
                source_field_name='from_user',
                target_field_name='to_user'
            )
            return manager

field.contribute_to_class(User, 'followers')
setattr(User, 'followers', FollowersDescriptor())


from django.db.models.signals import post_save

# Automatically add "blog" to following users 
#    after creating new account.
def user_post_save( sender, instance, created, *args, **kw ):
    if created:
        try:
            if instance.username <> 'blog': # ...
                user_to_follow = User.objects.get( username='blog' )
                instance.followers.follow( user_to_follow )
        except User.DoesNotExist:
           logger.error( "user `blog` doesn't exist [SKIPPING] " )


post_save.connect( user_post_save, sender=User )
post_save.connect( user_post_save, sender=TemporaryUser )
