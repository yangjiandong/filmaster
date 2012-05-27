import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'film20.settings'
from film20.followers.models import *
from film20.friends.models import *
from django.contrib.auth.models import User



def create_followers():
    """
       Takes friends and create followers from them
    """

    for friendship in Friendship.objects.all():
        u1 = friendship.from_user
        u2 = friendship.to_user
        u1.followers.follow(u2)
        u2.followers.follow(u1)

def main():
    create_followers()

if __name__ == "__main__":
    main()
