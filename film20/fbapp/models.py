import datetime

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.utils.translation import ungettext

from film20.showtimes.models import Channel
from film20.facebook_connect.models import FBUser
from film20.utils import cache

from film20.utils.db import FieldChangeDetectorMixin

class Tickets(models.Model):
    class Meta:
        verbose_name_plural = _("Tickets")
        ordering = ('-date', 'theater__name')

    theater = models.ForeignKey(Channel, limit_choices_to={'type':1})
    date = models.DateField()
    descr = models.CharField(max_length=128, blank=True)
    amount = models.IntegerField(default=1)

    def get_participants(self, contest):
        participants = ContestParticipation.objects.filter(ticket=self, contest=contest).exclude(user__username__startswith='fb-').exclude(is_active=False)
        return participants.order_by('-score', 'created_at')[:self.amount]

    def __unicode__(self):
        return u"%sx %s %s @ %s" % (self.amount, self.date, self.descr, self.theater)

class ContestManager( models.Manager ):
    def get_query_set( self ):
        return super( ContestManager, self ).get_query_set().filter( event__isnull=True, LANG=settings.LANGUAGE_CODE )


class Contest(models.Model, FieldChangeDetectorMixin):
    STATE_OPEN = 0
    STATE_CLOSED = 1

    CHOICES = (
        (STATE_OPEN, _("Open")),
        (STATE_CLOSED, _("Closed")),
    )
    
    class Meta:
        ordering = ('-final_date', )

    LANG = models.CharField( _( "LANG" ), max_length=2, default=settings.LANGUAGE_CODE )
    title = models.CharField(max_length=128, default='')
    descr = models.TextField(default='', blank=True)
    state = models.IntegerField(default=0, choices=CHOICES)
    final_date = models.DateField()
    # tickets = models.ManyToManyField( Tickets, verbose_name=_( "Tickets" ), null=True, blank=True )
    tickets_old = models.ManyToManyField( Tickets, verbose_name=_( "Tickets" ), null=True, blank=True, related_name='tickets_old' )

    objects = ContestManager()
    
    DETECT_CHANGE_FIELDS = ('state', )

    def score_board(self):
        return User.objects.filter(
                contestparticipation__contest=self.pk).\
            annotate(models.Sum('contestparticipation__score')).\
            order_by('-contestparticipation__score__sum')

    def __unicode__(self):
        return self.title

    def days_to_final( self ):
        return ( self.final_date - datetime.datetime.now().date() ).days

    def time_to_final(self):
        delta = datetime.datetime(*self.final_date.timetuple()[:3]) + datetime.timedelta(days=1) - datetime.datetime.now()
        return {
                'days': delta.days,
                'hours': delta.seconds / 3600,
                'minutes': (delta.seconds % 3600) / 60,
        }

    def prev_winners(self):
        from collections import defaultdict
        winners = defaultdict(set) # dictionary theater -> set of participants
        contests = Contest.objects.filter(
                    final_date__gt=self.final_date-datetime.timedelta(days=30),
                    state=self.STATE_CLOSED,
                )
        for c in contests:
            for t in c.tickets.all():
                winners[t.theater_id].update(i.fb_user_id for i in t.get_winners())
        return winners

    def compute_winners(self):
        prev_winners = self.prev_winners()
        for ticket in self.tickets.all():
            ticket.get_winners().update(state=ContestParticipation.STATE_RATINGS)
            latest_winners = prev_winners.get(ticket.theater_id, set())
            ids = [p.id for p in ticket.get_participants().filter(state=ContestParticipation.STATE_RATINGS) if p.fb_user_id not in latest_winners]
            ids = ids[:ticket.amount]
            ticket.get_participants().filter(id__in=ids).update(state=ContestParticipation.STATE_WON)

    @classmethod
    def post_save(cls, instance, *args, **kwargs):
        cache.delete(cache.Key('contest'))
        if instance.has_field_changed('state') and instance.state == cls.STATE_CLOSED:
            instance.compute_winners()

models.signals.post_save.connect(Contest.post_save, sender=Contest)

class ContestTickets(models.Model):
    class Meta:
        verbose_name_plural = _("Contest Tickets")

    contest = models.ForeignKey(Contest, related_name='tickets')
    theater = models.ForeignKey(Channel, limit_choices_to={'type':1})
    descr = models.CharField(max_length=128, blank=True)
    amount = models.IntegerField(default=1)

    def get_winners(self):
        return self.get_participants().filter(state=ContestParticipation.STATE_WON)
    
    def get_participants(self):
        participants = ContestParticipation.objects.filter(contest=self.contest_id, contest_ticket=self).exclude(user__username__startswith='fb-').exclude(is_active=False)
        return participants.order_by('-score', 'created_at')

    def __unicode__(self):
        return u"%sx %s @ %s" % (self.amount, self.descr, self.theater)

class ContestParticipation(models.Model):
    contest = models.ForeignKey(Contest, null=True, blank=True)
    user = models.ForeignKey(User)
    fb_user = models.ForeignKey(FBUser, null=True)
    ticket = models.ForeignKey(Tickets, blank=True, null=True)
    contest_ticket = models.ForeignKey(ContestTickets, null=True, blank=True)
    score = models.IntegerField(default=0)
    ratings_start_count = models.IntegerField(default=0)
    rated_count = models.IntegerField(default=0)
    quiz_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    STATE_NEW = 0
    STATE_AUTH = 1
    STATE_TICKET = 2
    STATE_QUIZ = 3
    STATE_RATINGS = 4
    STATE_WON = 5
    STATE_LOST = 6

    CHOICES = (
        (STATE_NEW, _("New")),
        (STATE_AUTH, _("Authorized")),
        (STATE_TICKET, _("Ticket")),
        (STATE_QUIZ, _("Quiz")),
        (STATE_RATINGS, _("Ratings")),
        (STATE_WON, _("Won")),
        (STATE_LOST, _("Lost")),
    )

    state = models.IntegerField(default=0, choices=CHOICES)
    wallpost_published = models.BooleanField(default=False)
    sent_invite_count = models.IntegerField(default=0)
    accepted_invites_count = models.IntegerField(default=0)

    def __unicode__(self):
        return self.user.username
    
    class Meta:
        unique_together = (('contest', 'fb_user'), ('contest', 'user'))

class Event( Contest ):
    APP_ID = models.CharField( _( "APP_ID" ), max_length=255, unique=True )
    APP_SECRET = models.CharField( _( "APP_SECRET" ), max_length=255 )

    slug = models.SlugField( _( "slug" ), unique=True )
    
    start_description = models.TextField( _( "start description" ), blank=True, null=True )
    end_description = models.TextField( _( "end description" ), blank=True, null=True )
    wallpost_description = models.TextField( _( "wallpost description" ), blank=True, null=True )

    def __unicode__( self ):
        return self.slug

    def get_absolute_url( self ):
        return 'http://apps.facebook.com/%s/' % self.APP_ID

    @property
    def score_board( self ):
        return FBUser.objects.filter(
                contestparticipation__contest=self.pk).\
                    annotate(score=models.Sum('contestparticipation__score')).\
                    order_by('-score')


