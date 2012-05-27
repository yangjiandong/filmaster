# -*- coding: utf-8 -*-
"""
Facebook Application
"""
import logging
logger = logging.getLogger(__name__)
import hmac, hashlib
import json
import datetime
import time
import random
from urllib import urlencode
from urllib2 import HTTPError

from django import http
from django.shortcuts import render, render_to_response
from django.conf import settings
from django.views.generic.base import View, TemplateView
from django.views.generic.detail import DetailView
from django.contrib import auth
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.views.decorators.cache import never_cache
from django.template import RequestContext
from django.utils.translation import gettext_lazy as _

from film20.facebook_connect import graph
from film20.facebook_connect.models import FBAssociation, FBUser, FBRequest
from film20.core.models import FilmRanking, Rating, Person, Country
from film20.core.urlresolvers import reverse as abs_reverse
from film20.fbapp.models import ContestTickets, Contest, ContestParticipation, Event
from film20.utils import cache
from film20.core import rating_helper
from film20.showtimes.models import Channel

class FBApp(View):
    APP_ID = settings.FBAPP_CONNECT_KEY 
    APP_SECRET = settings.FBAPP_CONNECT_SECRET

    LANDING_TEMPLATE = "fbapp/authorize.html"

    def signed_data(self, request):
        from film20.facebook_connect.utils import parse_signed_request
        return parse_signed_request(request.POST['signed_request'], self.APP_SECRET)

    def get(self, request, *args, **kwargs):
        return http.HttpResponseRedirect(self.fb_app_url() + '?' + request.META.get('QUERY_STRING', ''))

    def fb_app_url(self):
        return 'http://apps.facebook.com/%s/' % self.APP_ID

    def get_absolute_url( self ):
        return abs_reverse( fbapp )

    def post(self, request, *args, **kwargs):
        self.data = self.signed_data(request)

        if self.data is None:
            return http.HttpResponse("invalid signature")

        user_id = self.data.get('user_id')

        if not user_id:
            return self.landing_page(request)

        return self.canvas(request, **self.data)

    def landing_page(self, request):
        values = [('client_id',self.APP_ID),
                  ('redirect_uri', self.get_absolute_url() + '?' + request.META.get('QUERY_STRING', '')),
                  # TODO - add offline_access perm later
                  #('scope','offline_access,email'),
                  ('scope','email')]
        auth_url = "https://www.facebook.com/dialog/oauth?" + urlencode(values)

        request_ids = request.GET.get('request_ids')
        # request_ids = ','.join(str(r.id) for r in FBRequest.objects.all())
        if request_ids:
            requests = FBRequest.objects.filter(id__in=request_ids.split(','))
            inviting_users = set(req.sender for req in requests if req.data == 'invite')
        else:
            inviting_users = []

        return render(request, self.LANDING_TEMPLATE, {
            'auth_url': auth_url,
            'landing_page': not 'skip_landing_page' in request.GET,
            'APP_ID': self.APP_ID,
            'inviting_users': inviting_users,
        })

    def get_friends( self, fb_user ):
        return fb_user.friends.filter(contestparticipation__isnull=False).distinct()

    def get_context_data( self, request, user_id=None, oauth_token=None, **kwargs ):

        me = self.api.get('/me')

        fb_user = FBUser.create_or_update(me)

        try:
            assoc = FBAssociation.objects.get(fb_uid=user_id)
            user = assoc.user
            user = auth.authenticate(fb_uid=user_id)
            auth.login(request, user)
        except FBAssociation.DoesNotExist, e:
            if request.user.is_authenticated():
                user = request.user
                # auto create fbassociation
                FBAssociation.objects.create(
                        fb_uid = fb_user.id,
                        fb_user = fb_user,
                        user = user)
                FBUser.update_objects( self.api, '/me/friends', fb_user.friends )
            else:
                from film20.core.models import TemporaryUser
                user, created = TemporaryUser.objects.get_or_create(
                    username="fb-%s" % user_id,
                    defaults={'is_active':False},
                )
                if created:
                    FBUser.update_objects( self.api, '/me/friends', fb_user.friends )

                user.dirty = True 
                request._unique_user = user

        me['access_token'] = oauth_token

        request.session['user_details'] = me

        request.session['skip'] = 'skip' in request.GET

        return {
            'user': user,
            'data': json.dumps(self.data),
            'details': json.dumps(me),
            'friends': self.get_friends( fb_user ),
            'APP_ID': self.APP_ID,
            'auto_fb_user': self.request.unique_user.username.startswith('fb-'),
        }

    def canvas(self, request, user_id=None, oauth_token=None, **kw):
        self.api = graph.API( oauth_token )
        ret = self.process_requests( request, user_id )
        if ret:
            return ret
        context_data = self.get_context_data( request, user_id, oauth_token )
        return render( request, context_data.get( "template", "fbapp/canvas.html" ), context_data )


    def process_requests(self, request, user_id):
        """
        example request:
        {u'from': {u'name': u'Mariusz Krynski', u'id': u'100003342612804'},
         u'to': {u'name': u'Mariusz Kry\u0144ski', u'id': u'1576823518'},
         u'application': {u'name': u'FlmApp', u'id': u'289754501067521'},
         u'created_time': u'2012-01-13T13:38:20+0000',
         u'message': u'Zagraj o Bilety !',
         u'data': u'ticket_contest', u'id': u'326963054003146'}
        """
        self.fb_requests = []
        request_ids = request.GET.get('request_ids')
        signup = False
        if request_ids:
            ids = request_ids.split(',')
            for id in ids:
                req = self.api.get("/%s_%s" % (id, user_id))
                logger.info("request: %r, user_id: %r", req, user_id)
                try:
                    self.api.delete('/%s_%s' % (id, user_id))
                except HTTPError, e:
                    pass

                if req and str(req['to']['id']) == str(user_id):
                    request_name = req.get('data')
                    if request_name == 'ticket_contest':
                        request.session['invite_request'] = req
                    elif request_name == 'invite':
                        signup = True

        if signup:
            return http.HttpResponse("""
            <script>top.location.href="%s"</script>
            """ % abs_reverse('fb_begin'))

fbapp = never_cache(FBApp.as_view())

class ResultsView(DetailView):
    model = Contest
    template_name = 'fbapp/results.html'

    def get_object(self):
        if not 'pk' in self.kwargs:
            obj = Contest.objects.filter(state=Contest.STATE_CLOSED)
            obj = obj and obj[0]
            if not obj:
                raise http.Http404
            return obj
        return super(ResultsView, self).get_object()

    def get_context_data(self, *args, **kw):
        context = super(ResultsView, self).get_context_data(*args, **kw)
        context['tickets'] = self.object.tickets.all()
#        for t in context['tickets']:
#            t.participants = t.get_participants(self.object)
        return context

results = ResultsView.as_view()

class AjaxView(TemplateView):

    @never_cache
    def dispatch(self, request, *args, **kw):
        self.user_details = request.session.get('user_details')
        if not self.user_details:
            return http.HttpResponseRedirect('..')
        return super(AjaxView, self).dispatch(request, *args, **kw)

    def get_contest( self ):
        contest_key = cache.Key("contest")
        contest = cache.get(contest_key)
        if not contest:
            try:
                contest = Contest.objects.get(state=Contest.STATE_OPEN)
            except Contest.DoesNotExist:
                contest = Contest.objects.all().order_by('-final_date')[0]

            if contest.final_date < datetime.date.today():
                contest.state = Contest.STATE_CLOSED
                contest.save()
                contest = Contest.objects.get(id=contest.id)
            cache.set(contest_key, contest)
        return contest

    def get_context_data(self, *args, **kw):
        context = super(AjaxView, self).get_context_data(*args, **kw)

        self.contest = self.get_contest()

        context['user_details'] = self.user_details
        context['contest'] = self.contest
        context['APP_ID'] = settings.FBAPP_CONNECT_KEY
        context['auto_fb_user'] = self.request.unique_user.username.startswith('fb-')
        return context

    def add_invite_points(self):
        invite_request = self.request.session.get('invite_request')
        if invite_request:
            del self.request.session['invite_request']
            fb_user = invite_request['from']['id']
            try:
                participant = ContestParticipation.objects.get(
                                fb_user=fb_user,
                                contest=self.contest
                            )
                participant.score += 5
                participant.save()
            except ContestParticipation.DoesNotExist, e:
                pass

class FBAppMain(FBApp):
    def get(self, request, *args, **kw):
        return self.landing_page(request)

main = FBAppMain.as_view()

from film20.account.forms import SSORegistrationForm, LoginForm

class LoginOrSignupView( AjaxView ):
    template_name='fbapp/login_or_signup.html'
    on_success_view = "fbapp_the_end"

    def get_context_data( self, *args, **kw ):
        context = super( LoginOrSignupView, self ).get_context_data( *args, **kw )
        context.update({
            'login_form': self.login_form,
            'signup_form': self.signup_form
        })
        return context

    def get_login_form( self ):
        return LoginForm()

    def get_signup_form( self ):
        user_details = self.user_details
        initial = dict(
            username=user_details.get('username', user_details.get('name')),
            email=user_details.get('email'),
        )
        return SSORegistrationForm( initial=initial, request=self.request )

    def get( self, request, *args, **kw ):
        self.login_form = self.get_login_form()
        self.signup_form = self.get_signup_form()
        return super( LoginOrSignupView, self ).get( request, *args, **kw )

    def post( self, request, *args, **kw ):
        user_details = self.user_details
        is_signup = 'signup' in request.POST

        tmp_user = request.unique_user

        if is_signup:
            self.form = SSORegistrationForm(self.request.POST, request=self.request)
            self.signup_form = self.form
            self.login_form = self.get_login_form()
        else:
            self.form = LoginForm( self.request.POST )
            self.login_form = self.form
            self.signup_form = self.get_signup_form()
        
        context = self.get_context_data(*args, **kw)

        if self.form.is_valid():
            if is_signup:
                user = self.form.save()
            else:
                user = self.form.user

            fb_user = FBUser.create_or_update(user_details)
            FBAssociation.objects.create(
                    fb_uid = fb_user.id,
                    fb_user = fb_user,
                    user = user)
            user = auth.authenticate(fb_uid=fb_user.id)
            auth.login(self.request, user)
            participation = ContestParticipation.objects.get(contest=self.contest, fb_user=fb_user)
            participation.user = user
            participation.save()

            if not is_signup and tmp_user and tmp_user.username.startswith('fb-'):
                # user logged in, remove temporary user
                tmp_user.delete()

            return http.HttpResponseRedirect(reverse(self.on_success_view))

        return self.render_to_response(context)

login_or_signup = LoginOrSignupView.as_view()


class ViralView(AjaxView):
    template_name='fbapp/viral.html'

    def get_context_data(self, *args, **kw):
        context = super(ViralView, self).get_context_data(*args, **kw)

        contest = self.get_contest()
        participant = ContestParticipation.objects.get(
                        user=self.request.unique_user,
                        contest=contest
                    )

        context['participant'] = participant
        context['wallpost'] = settings.FBAPP.get('points').get('wallpost', 0)
        context['invited_friend'] = settings.FBAPP.get('points').get('invited_friend', 0)

        return context

    def post(self, request, *args, **kw):
        context = self.get_context_data(*args, **kw)
        contest = context.get('contest')
        participant = context.get('participant')
        if not contest or not participant:
            return http.HttpResponse('error')
        if 'invites_sent' in self.request.POST:
            to = filter(bool, self.request.POST['to'].split(','))
            participant.sent_invite_count += len('to')
            participant.save()
        elif 'wallpost_published' in self.request.POST:
            participant.wallpost_published = True
            participant.score += settings.FBAPP.get('points').get('wallpost', 0)
            participant.save()
        return http.HttpResponse('ok')

viral_view = never_cache(ViralView.as_view())

class TheEnd(AjaxView):
    template_name='fbapp/the_end.html'
    
    def get( self, request, *args, **kwargs ):
        ret = super( TheEnd, self ).get( request, *args, **kwargs )
        self.add_invite_points()
        return ret

the_end = never_cache(TheEnd.as_view())

class TermsView(TemplateView):
    template_name='fbapp/terms.html'

terms = TermsView.as_view()

class ContactView(TemplateView):
    template_name='fbapp/contact.html'

contact = ContactView.as_view()

class ChooseTicket(AjaxView):
    """
    User takes ticket for movie
    """
    template_name = 'fbapp/tickets.html'

    def get(self, *args, **kw):
        if self.request.session.get('skip'):
            return http.HttpResponseRedirect(reverse(rate_films))

        self.get_context_data()

        contest = self.get_contest()

        tickets = contest.tickets.all()

        fb_uid = self.user_details['id']
        prev_winners = contest.prev_winners()
        theaters = set(theater for theater, winners in prev_winners.items() if fb_uid in winners)
        theaters = [Channel.objects.get(id=id) for id in theaters]
        try:
            last_contest = Contest.objects.all().order_by('-final_date')[0]
            score_board = last_contest.score_board
        except Contest.DoesNotExist:
            last_contest = None
            score_board = None

        try:
            participant = ContestParticipation.objects.get(
                            user=self.request.unique_user,
                            contest=contest
                        )
            if participant.state < ContestParticipation.STATE_RATINGS:
                participant.score = 0
                participant.rated_count = 0
                participant.quiz_count = 0
                participant.save()
                key = cache.Key("questions_", self.request.unique_user)
                cache.delete(key)
                participant = None
        except ContestParticipation.DoesNotExist:
            participant = None

        return render(self.request, self.template_name, {
            'tickets': tickets or [],
            'contest': self.contest,
            'theaters': theaters,
            'last_contest': last_contest,
            'score_board': score_board,
            'participant': participant,
            })

    def post(self, *args, **kw):
        ticket_id = int(self.request.POST['ticket'])
        if not ticket_id:
            return http.HttpResponseRedirect(reverse("fbapp_choose_ticket"))
        ticket = ContestTickets.objects.get(id=ticket_id)

        contest = self.get_contest()

        try:
            participant = ContestParticipation.objects.get(
                            contest=contest,
                            user=self.request.unique_user
                        )
        except ContestParticipation.DoesNotExist:
            fb_user = FBUser.create_or_update(self.user_details)
            ratings_cnt = len(rating_helper.get_user_ratings(self.request.unique_user).keys())
            participant = ContestParticipation.objects.create(
                            contest=contest,
                            user=self.request.unique_user,
                            fb_user=fb_user,
                            contest_ticket=ticket,
                            score=5,
                            ratings_start_count = ratings_cnt,
                        )

        participant.state = ContestParticipation.STATE_TICKET
        participant.contest_ticket = ticket
        participant.save()

        return http.HttpResponseRedirect(reverse("fbapp_quiz"))

choose_ticket = ChooseTicket.as_view()

class RateFilms(AjaxView):
    """
    User can rate movies
    """
    template_name = "fbapp/rate_movies2.html"
    empty = "fbapp/empty.html"

    @property
    def movies_to_rate( self ):
        return settings.FBAPP.get('config').get('movies_to_rate_on_page', 3)

    def calculate_progress(self, participant):
        ratings_cnt = len(rating_helper.get_user_ratings(participant.user).keys())
        progress_max = settings.FBAPP.get('config').get('movies_to_rate_for_progress', 6)
        progress_value = max(0, ratings_cnt - participant.ratings_start_count)
        progress_value = min(progress_value, progress_max)
        progress_left = progress_max - progress_value
        progress_percent = progress_value * 100 / progress_max
        
        if progress_value > participant.rated_count:
            n = progress_value - participant.rated_count
            participant.state = ContestParticipation.STATE_RATINGS
            participant.rated_count = progress_value
            participant.score += n * settings.FBAPP.get('points').get('rated_movie', 10)
            participant.save()

        return {
                'progress_max': progress_max,
                'progress_value': progress_value,
                'progress_left': progress_left,
                'progress_percent': progress_percent,
                'participant': participant,
        }

    def get(self, *args, **kw):
        contest = self.get_contest()
        participant = ContestParticipation.objects.get(user=self.request.unique_user, contest=contest)

        if participant.state >= ContestParticipation.STATE_QUIZ:
            self.request.contest = True

        context = self.get_context_data()
        context.update(self.calculate_progress(participant))
        return render( self.request, self.template_name, context )

    def post(self, *args, **kwargs):
        contest = self.get_contest()
        participant = ContestParticipation.objects.get(
                        user=self.request.unique_user,
                        contest=contest
                    )
        context = self.get_context_data()
        context.update(self.calculate_progress(participant))
        return render(self.request, 'fbapp/rate_movies_update.html', context) 

rate_films = RateFilms.as_view()

class QuizView(AjaxView):
    """
    QuizView prepares view for contest
    """
    template_name = 'fbapp/quiz_questions.html'
    summary_template_name = 'fbapp/quiz_summary.html'
    on_start = 'fbapp/quiz_info.html'
    
    def get_next_step( self ):
        return reverse( "fbapp_rate_films" )

    def prepare_data_for_quiz(self):
        key = cache.Key("user_films_", self.request.unique_user)
        list_of_films = cache.get(key)
        if not list_of_films:
            ranking = list(FilmRanking.objects.filter(type=Rating.TYPE_FILM).
                           exclude(Q(film__production_country_list__isnull=True) |
                                   Q(film__production_country_list="")).
                           select_related('film', 'film__directors',
                                          'film__actors').
                           order_by('-number_of_votes')[:settings.FBAPP.get('config').get('no_of_movies', 500)])
            random.shuffle(ranking)
            films = ranking[:settings.FBAPP.get('config').get('no_of_questions', 10)+1]
            list_of_films = []
            for rank in films:
                title = rank.film

                directors = rank.film.get_directors()
                list_of_directors = []
                for director in directors:
                    list_of_directors.append({'director': director})

                actors = rank.film.top_actors()
                list_of_actors = []
                for actor in actors:
                    list_of_actors.append({'actor': actor.person,
                                           'character': actor.character})

                release_year = rank.film.release_year
                countries = rank.film.production_country_list

                movie = {'title': title, 'year': release_year,
                         'actors': list_of_actors, 'directors': list_of_directors,
                         'countries': countries, 'question': []}
                list_of_films.append(movie)
                cache.set(key, list_of_films)
        return list_of_films

    def generate_year_question(self, list_of_movies):
        for film in list_of_movies:
            correct_year = film['year']
            x = random.uniform(1, settings.FBAPP.get('config').get('movie_years', 3))
            y = random.uniform(1, settings.FBAPP.get('config').get('movie_years', 3))

            up_year = int(correct_year + round(x))
            down_year = int(correct_year - round(y))

            if up_year > datetime.datetime.now().year:
                if correct_year != datetime.datetime.now().year:
                    up_year = datetime.datetime.now().year
                else:
                    up_year = up_year - 1

            if down_year == up_year:
                down_year = down_year - 1

            year_choices = [correct_year, up_year, down_year]
            random.shuffle(year_choices)
            #question = "W którym roku zrealizowano film %s" % film['title'].get_title()
            question = _( "In which year was %(film)s released" ) % { 'film': film['title'].get_title() }

            photo = film['title'].get_absolute_image_url()
            film['question'].append(dict(
                question=question,
                answer=correct_year,
                choices=year_choices,
                photo=photo
            ))
            del film['year']
    
    def generate_director_question(self, list_of_movies):
        directors = list(Person.objects.filter(is_director=True, is_actor=False).
                         order_by('-director_popularity')[:settings.FBAPP.get('config').get('no_of_directors', 50)])
        
        for film in list_of_movies:
            director_choices = []
            random.shuffle(directors)
            chosen_directors = directors[:2]
            correct_directors = film['directors']
            for director in chosen_directors:
                for correct in correct_directors:
                    if director == correct['director']:
                        random.shuffle(directors)
                        chosen_directors.append(directors[0])
                director_choices.append(director)
            director_choices.append(correct_directors[0]['director'])
            random.shuffle(director_choices)
            #question = "Który reżyser nakręcił film %s" % film['title']
            question = _( "Who was the director of %(film)s" ) % { 'film': film['title'] }

            photo = film['title'].get_absolute_image_url()
            film['question'].append(dict(
                question=question,
                answer=correct_directors[0]['director'].id,
                choices=director_choices,
                photo=photo,
            ))
            del film['directors']
    
    def generate_actor_question(self, list_of_movies):
        actors = list(Person.objects.filter(is_actor=True, is_director=False).
                      order_by('-actor_popularity')[:settings.FBAPP.get('config').get('no_of_actors', 50)])
        for film in list_of_movies:
            actor_choices = []
            random.shuffle(actors)
            correct_actors = film['actors']
            
            all_actors = []
            for actor in correct_actors:
                all_actors.append(actor['actor'])
            random.shuffle(all_actors)

            chosen_actors = actors[:2]
            for actor in chosen_actors:
                for correct in correct_actors:
                    if actor == correct['actor']:
                        random.shuffle(actors)
                        chosen_actors.append(actors[0])
                actor_choices.append(actor.person)
            if len( all_actors ) == 0:
                continue
            actor_choices.append(all_actors[0].person)
            random.shuffle(actor_choices)
            #question = "Który aktor wystąpił w filmie %s" % film['title']
            question = _( "Which actor played in %(film)s" ) % { 'film': film['title'] }

            photo = film['title'].get_absolute_image_url()
            film['question'].append(dict(
                question=question,
                answer=all_actors[0].id,
                choices=actor_choices,
                photo=photo
            ))

    def generate_character_question(self, list_of_movies):
        # TODO: Exclude movies without characters!      
        for film in list_of_movies:
            character_choices = []
            actors = film['actors']   
            for actor in actors[1:]:
                character_choices.append(actor['actor'])                
                random.shuffle(character_choices)
            
            character_choices = character_choices[:2]
            if len( actors ) == 0:
                continue
            character_choices.append(actors[0]['actor'])
            random.shuffle(character_choices)
            #question = "Który aktor zagrał w filmie %s postać %s" % (film['title'],actors[0]['character'])
            question = _( "Which actor played %(character)s in %(film)s" ) % { 'character': actors[0]['character'], 'film': film['title'] }

            photo = film['title'].get_absolute_image_url()
            film['question'].append(dict(
                question=question,
                answer=actors[0]['actor'].id,
                choices=character_choices,
                photo=photo
            ))
            del film['actors']

    def generate_gender_question(self, list_of_movies):
        pass

    def generate_country_question(self, list_of_movies):
        for film in list_of_movies:
            country_choices = []
            film_countries = film['countries'].split(',')
            other_countries = list(Country.objects.exclude(country__in=film_countries))
            random.shuffle(other_countries)
            for country in other_countries[:2]:
                country_choices.append(country)
            try:
                answer = Country.objects.get(country = film_countries[0])
            except:
                answer = Country.objects.filter(country = film_countries[0])
                answer = answer[0]

            country_choices.append(answer)
            random.shuffle(country_choices)

            #question = "W którym kraju wyprodukowano film %s" % (film['title'].get_title(),)
            question = _( "In which country was %(film)s produced" ) % { 'film': film['title'].get_title() }

            photo = film['title'].get_absolute_image_url()
            film['question'].append(dict(
                question=question,
                answer=answer.id,
                choices=country_choices,
                photo=photo
            ))
            del film['countries']

    def quiz_mixer(self):
        list_of_movies = self.prepare_data_for_quiz()
        self.generate_year_question(list_of_movies)
        self.generate_director_question(list_of_movies)
        self.generate_actor_question(list_of_movies)
        self.generate_character_question(list_of_movies)
        self.generate_country_question(list_of_movies)

        questions = []
        for film in list_of_movies:
            rand = int(random.uniform(0, len(film['question'])))
            questions.append(film['question'][rand])
        return questions

    def check_answer(self, serv_tstamp):
        question_key = cache.Key("answer_", self.request.unique_user)
        question = cache.get(question_key)

        if question:
            answer = question.get('answer', '')
            choice = int(self.request.POST.get('choice', 0))
            user_tstamp = float(self.request.POST.get('tstamp'))
            if answer == choice:
                self.count_points(user_tstamp, serv_tstamp)
        cache.delete(question_key)

    def count_points(self, user_tstamp, serv_tstamp):
        quiz_points_key = cache.Key("points_", self.request.unique_user)
        quiz_points = cache.get(quiz_points_key)
        cache.delete(quiz_points_key)

        if not quiz_points:
            quiz_points = 0

        tdelta = serv_tstamp - user_tstamp
        tdelta = int(round(tdelta))

        quiz_points += settings.FBAPP.get('points').get('seconds').get(tdelta, 0)
        cache.set(quiz_points_key, quiz_points)
        return quiz_points

    def get(self, *args, **kw):
        context = self.get_context_data()

        contest = self.get_contest()
        participant = ContestParticipation.objects.get(user=self.request.unique_user, contest=contest)
        if participant.state >= ContestParticipation.STATE_QUIZ:
            return http.HttpResponseRedirect(self.get_next_step())

        key = cache.Key("questions_", self.request.unique_user)
        questions = cache.get(key)
        if not questions:
            questions = self.quiz_mixer()        
            cache.set(key, questions)
        return render(self.request, self.on_start, context)

    def post(self, *args, **kw):
        key = cache.Key("questions_", self.request.unique_user)
        questions = cache.get(key)

        if "start" not in self.request.POST:
            self.check_answer(time.time())

        if not questions:
            return self.on_end_questions()

        question = questions.pop()
        if question:
            cache.delete(key) # delete cache for questions
            cache.set(key, questions) # set cache for questions-1
            key = cache.Key("answer_", self.request.unique_user)
            cache.set(key, question) # set cache for user answer

        context = self.get_context_data()
        context.update({
            'question': question or [],
            'tstamp': time.time(),
            'progress': (100-len(questions)*10),
            'answered': 10-len(questions)
        })
        return render(self.request, self.template_name, context )

    def on_end_questions( self ):
        points = self.add_points()
        context = self.get_context_data()
        context.update({ 'score': points })
        return render( self.request, self.summary_template_name, context )

    def add_points(self):
        quiz_points_key = cache.Key("points_", self.request.unique_user)
        quiz_points = cache.get(quiz_points_key)

        contest = self.get_contest()
        participant = ContestParticipation.objects.get(user=self.request.unique_user, contest=contest)

        if participant.state == ContestParticipation.STATE_TICKET:
            participant.quiz_count = quiz_points
            participant.score += quiz_points
            participant.state = ContestParticipation.STATE_QUIZ
            participant.save()
        cache.delete(quiz_points_key)
        return participant.score


quiz = QuizView.as_view()

# EVENTS

from django.views.generic.detail import SingleObjectMixin
class EventMixin( SingleObjectMixin ):
    model = Event

    def get_participant( self ):
        contest = self.get_object()
        fb_user = FBUser.create_or_update( self.request.session['user_details'] )
        try:
            participant = ContestParticipation.objects.get( contest=contest, fb_user=fb_user )
            if participant.user != self.request.unique_user:
                participant.user = self.request.unique_user
                participant.save()
        except ContestParticipation.DoesNotExist:
            ratings_cnt = len(rating_helper.get_user_ratings(self.request.unique_user).keys())
            participant = ContestParticipation.objects.create(
                    contest=contest,
                    user=self.request.unique_user, 
                    ratings_start_count = ratings_cnt,
                    fb_user=fb_user, state=ContestParticipation.STATE_TICKET
            )
        return participant

    def get_context_data( self, *args, **kwargs ):
        context = super( EventMixin, self ).get_context_data( *args, **kwargs )
        context['APP_ID'] = self.get_object().APP_ID
        return context



class FBAppEvent( FBApp, EventMixin ):

    LANDING_TEMPLATE = "fbapp/event/authorize.html"

    def _override( self ):
        self.object = self.get_object()
        self.APP_ID = self.object.APP_ID
        self.APP_SECRET = self.object.APP_SECRET.encode( 'utf-8' )

    def get_absolute_url( self ):
        return abs_reverse( event, args=[self.get_object().slug ] )

    def get_context_data( self, request, user_id=None, oauth_token=None, **kwargs ):
        context_data = super( FBAppEvent, self ).get_context_data( request, user_id, oauth_token, **kwargs )
        context_data.update({
            'event'      : self.object,
            'participant': self.get_participant(),
            'template'   : 'fbapp/event/canvas.html'
        })
        return context_data

    def get_friends( self, fb_user ):
        return fb_user.friends.filter( contestparticipation__contest=self.get_object() ).distinct()

    def get( self, request, *args, **kwargs ):
        self._override()
        return super( FBAppEvent, self ).get( request, *args, **kwargs )

    def post( self, request, *args, **kwargs ):
        self._override()
        return super( FBAppEvent, self ).post( request, *args, **kwargs )

    def canvas( self, request, user_id=None, oauth_token=None, **kwargs ):
        parent = super( FBAppEvent, self ).canvas( request, user_id, oauth_token, **kwargs )
        participant = self.get_participant()
        if participant.state >= ContestParticipation.STATE_QUIZ:
            self.api = graph.API( oauth_token )
            ret = self.process_requests( request, user_id )
            if ret:
                return ret
            return http.HttpResponseRedirect( abs_reverse( event_viral, args=[self.object.slug]) )
        return parent


class EventQuiz( QuizView, EventMixin ):

    template_name = 'fbapp/event/quiz_questions.html'
    summary_template_name = 'fbapp/event/quiz_summary.html'
    on_start = 'fbapp/event/quiz_info.html'

    def get_next_step( self ):
        return reverse( "event_viral", args=[ self.get_object().slug ] )

    def get_contest( self ):
        return self.get_object()

    def get_context_data( self ):
        context = super( EventQuiz, self ).get_context_data()
        context.update({
            'participant': self.get_participant(),
            'APP_ID': self.get_contest().APP_ID
        })
        return context

    def get( self, *args, **kwargs ):
        if 'ticket' in self.request.GET:
            contest = self.get_contest()
            try:
                ticket = contest.tickets.get( pk=int( self.request.GET['ticket'] ) )
                participant = ContestParticipation.objects.get( contest=self.get_contest(), user=self.request.unique_user )
                participant.contest_ticket = ticket
                participant.save()
            except Ticket.DoesNotExist:
                pass # TODO: display error message

        return super( EventQuiz, self ).get( *args, **kwargs )

    def on_end_questions( self ):
        super( EventQuiz, self ).on_end_questions()
        return http.HttpResponseRedirect( abs_reverse( event_viral, args=[self.get_contest().slug]) )


class EventRateFilms( RateFilms, EventMixin ):
    template_name = "fbapp/event/rate_movies.html"
    movies_to_rate = 6

    def get_contest( self ):
        return self.get_object()


class EventViral( ViralView, EventMixin ):
    template_name='fbapp/event/quiz_summary.html'

    def get_contest( self ):
        return self.get_object()

    def get_context_data( self, *args, **kwargs ):
        context = super( EventViral, self ).get_context_data( *args, **kwargs )
        context['APP_ID'] = self.get_contest().APP_ID
        return context

class EventScoreBoard( TemplateView, EventMixin ):
    template_name = "fbapp/event/score_board.html"

    def get_context_data( self, *args, **kwargs ):
        event = self.get_object();
        context = super( EventScoreBoard, self ).get_context_data( *args, **kwargs )
        context.update({
            'event': event,
            'score_board': event.score_board
        })
        return context

event = never_cache( FBAppEvent.as_view() )
event_quiz = EventQuiz.as_view()
event_rate_films = EventRateFilms.as_view()
event_viral = EventViral.as_view()
event_score_board = EventScoreBoard.as_view()
