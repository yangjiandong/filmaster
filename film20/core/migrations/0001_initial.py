# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Object'
        db.create_table('core_object', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type', self.gf('django.db.models.fields.IntegerField')()),
            ('permalink', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('status', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('version', self.gf('django.db.models.fields.IntegerField')()),
            ('number_of_comments', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('core', ['Object'])

        # Adding model 'LocalizedProfile'
        db.create_table('core_localizedprofile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('LANG', self.gf('django.db.models.fields.CharField')(default='en', max_length=2)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('blog_title', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
        ))
        db.send_create_signal('core', ['LocalizedProfile'])

        # Adding unique constraint on 'LocalizedProfile', fields ['user', 'LANG']
        db.create_unique('core_localizedprofile', ['user_id', 'LANG'])

        # Adding model 'Profile'
        db.create_table('core_profile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], unique=True)),
            ('date', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('country', self.gf('film20.userprofile.countries.CountryField')(max_length=2, null=True, blank=True)),
            ('latitude', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=10, decimal_places=6, blank=True)),
            ('longitude', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=10, decimal_places=6, blank=True)),
            ('location', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('gender', self.gf('django.db.models.fields.CharField')(max_length=1, blank=True)),
            ('website', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('twitter_access_token', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('twitter_user_id', self.gf('django.db.models.fields.CharField')(max_length=32, null=True, blank=True)),
            ('foursquare_access_token', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('foursquare_user_id', self.gf('django.db.models.fields.CharField')(max_length=32, null=True, blank=True)),
            ('iphone_token', self.gf('django.db.models.fields.CharField')(max_length=64, null=True, blank=True)),
            ('mobile_platform', self.gf('django.db.models.fields.CharField')(max_length=16, null=True, blank=True)),
            ('mobile_first_login_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('mobile_last_login_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('mobile_login_cnt', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('jabber_id', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('gg', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('msn', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('icq', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('aol', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('facebook_name', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('myspace_name', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('criticker_name', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('imdb_name', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('metacritic_name', self.gf('django.db.models.fields.CharField')(max_length=128, blank=True)),
            ('LANG', self.gf('django.db.models.fields.CharField')(default='en', max_length=2)),
            ('registration_source', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('timezone_id', self.gf('django.db.models.fields.CharField')(max_length=40, null=True, blank=True)),
            ('recommendations_status', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('recommendations_notice_sent', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('core', ['Profile'])

        # Adding model 'Person'
        db.create_table('core_person', (
            ('image', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True, blank=True)),
            ('hires_image', self.gf('django.db.models.fields.files.ImageField')(max_length=256, null=True, blank=True)),
            ('imdb_code', self.gf('django.db.models.fields.CharField')(max_length=128, unique=True, null=True, blank=True)),
            ('parent', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['core.Object'], unique=True, primary_key=True)),
            ('tmdb_import_status', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('surname', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('day_of_birth', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('month_of_birth', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('year_of_birth', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('gender', self.gf('django.db.models.fields.CharField')(max_length=1, null=True, blank=True)),
            ('is_director', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_actor', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_writer', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('actor_popularity', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('director_popularity', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('writer_popularity', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('actor_popularity_month', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('director_popularity_month', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('writer_popularity_month', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('verified_imdb_code', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('core', ['Person'])

        # Adding model 'Country'
        db.create_table('core_country', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('country', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
        ))
        db.send_create_signal('core', ['Country'])

        # Adding model 'Film'
        db.create_table('core_film', (
            ('image', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True, blank=True)),
            ('hires_image', self.gf('django.db.models.fields.files.ImageField')(max_length=256, null=True, blank=True)),
            ('imdb_code', self.gf('django.db.models.fields.CharField')(max_length=128, unique=True, null=True, blank=True)),
            ('parent', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['core.Object'], unique=True, primary_key=True)),
            ('tmdb_import_status', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('verified_imdb_code', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('title_normalized', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('criticker_id', self.gf('django.db.models.fields.CharField')(max_length=16, null=True, blank=True)),
            ('release_year', self.gf('django.db.models.fields.IntegerField')()),
            ('release_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('production_country_list', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('is_enh9', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('popularity', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('popularity_month', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('core', ['Film'])

        # Adding M2M table for field directors on 'Film'
        db.create_table('core_film_directors', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('film', models.ForeignKey(orm['core.film'], null=False)),
            ('person', models.ForeignKey(orm['core.person'], null=False))
        ))
        db.create_unique('core_film_directors', ['film_id', 'person_id'])

        # Adding M2M table for field writers on 'Film'
        db.create_table('core_film_writers', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('film', models.ForeignKey(orm['core.film'], null=False)),
            ('person', models.ForeignKey(orm['core.person'], null=False))
        ))
        db.create_unique('core_film_writers', ['film_id', 'person_id'])

        # Adding M2M table for field production_country on 'Film'
        db.create_table('core_film_production_country', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('film', models.ForeignKey(orm['core.film'], null=False)),
            ('country', models.ForeignKey(orm['core.country'], null=False))
        ))
        db.create_unique('core_film_production_country', ['film_id', 'country_id'])

        # Adding model 'ObjectLocalized'
        db.create_table('core_objectlocalized', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Object'])),
            ('tag_list', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('LANG', self.gf('django.db.models.fields.CharField')(default='en', max_length=2)),
        ))
        db.send_create_signal('core', ['ObjectLocalized'])

        # Adding model 'SearchKey'
        db.create_table('core_searchkey', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('object', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Object'])),
            ('object_localized', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.ObjectLocalized'], null=True, blank=True)),
            ('key_normalized', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('key_root', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('key_letters', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('text_length', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('core', ['SearchKey'])

        # Adding model 'FilmLocalized'
        db.create_table('core_filmlocalized', (
            ('object_localized', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['core.ObjectLocalized'], unique=True, primary_key=True)),
            ('film', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Film'])),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('title_normalized', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=15000, null=True, blank=True)),
            ('fetched_description', self.gf('django.db.models.fields.CharField')(max_length=15000, null=True, blank=True)),
            ('fetched_description_url', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('fetched_description_url_text', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('fetched_description_type', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('release_year', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('release_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
        ))
        db.send_create_signal('core', ['FilmLocalized'])

        # Adding model 'ModeratedFilmLocalized'
        db.create_table('core_moderatedfilmlocalized', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('moderation_status', self.gf('django.db.models.fields.IntegerField')(default=-1)),
            ('moderation_status_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('moderation_status_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='moderatedfilmlocalized_moderated_objects', null=True, to=orm['auth.User'])),
            ('rejection_reason', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('LANG', self.gf('django.db.models.fields.CharField')(default='en', max_length=2)),
            ('film', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Film'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('tag_list', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=15000, null=True, blank=True)),
        ))
        db.send_create_signal('core', ['ModeratedFilmLocalized'])

        # Adding model 'PersonLocalized'
        db.create_table('core_personlocalized', (
            ('object_localized', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['core.ObjectLocalized'], unique=True, primary_key=True)),
            ('person', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Person'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('surname', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal('core', ['PersonLocalized'])

        # Adding model 'Character'
        db.create_table('core_character', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('person', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Person'])),
            ('film', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Film'])),
            ('importance', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('character', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('description_lead', self.gf('django.db.models.fields.CharField')(max_length=350, null=True, blank=True)),
            ('description_full', self.gf('django.db.models.fields.CharField')(max_length=1000, null=True, blank=True)),
            ('image', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True, blank=True)),
            ('image_thumb', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True, blank=True)),
            ('image_thumb_lost', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True, blank=True)),
            ('LANG', self.gf('django.db.models.fields.CharField')(default='en', max_length=2)),
        ))
        db.send_create_signal('core', ['Character'])

        # Adding model 'Rating'
        db.create_table('core_rating', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Object'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('film', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='film_ratings', null=True, to=orm['core.Film'])),
            ('actor', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='rated_as_actor', null=True, to=orm['core.Person'])),
            ('director', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='rated_as_director', null=True, to=orm['core.Person'])),
            ('rating', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('normalized', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=6, decimal_places=4, blank=True)),
            ('guess_rating_alg1', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=6, decimal_places=4, blank=True)),
            ('guess_rating_alg2', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=6, decimal_places=4, blank=True)),
            ('type', self.gf('django.db.models.fields.IntegerField')()),
            ('number_of_ratings', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('last_displayed', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('first_rated', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('last_rated', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('number_of_comments', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('core', ['Rating'])

        # Adding model 'FilmRanking'
        db.create_table('core_filmranking', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('film', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Film'])),
            ('type', self.gf('django.db.models.fields.IntegerField')()),
            ('average_score', self.gf('django.db.models.fields.DecimalField')(max_digits=4, decimal_places=2)),
            ('number_of_votes', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('core', ['FilmRanking'])

        # Adding model 'ShortReview'
        db.create_table('core_shortreview', (
            ('parent', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['core.Object'], unique=True, primary_key=True)),
            ('kind', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('object', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='short_reviews', null=True, to=orm['core.Object'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('rating', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='short_reviews', null=True, to=orm['core.Rating'])),
            ('review_text', self.gf('django.db.models.fields.CharField')(max_length=1000)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')()),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('LANG', self.gf('django.db.models.fields.CharField')(default='en', max_length=2)),
        ))
        db.send_create_signal('core', ['ShortReview'])

        # Adding model 'ShortReviewOld'
        db.create_table('core_shortreviewold', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('rating', self.gf('django.db.models.fields.related.ForeignKey')(related_name='short_reviewsold', to=orm['core.Rating'])),
            ('review_text', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('LANG', self.gf('django.db.models.fields.CharField')(default='en', max_length=2)),
        ))
        db.send_create_signal('core', ['ShortReviewOld'])

        # Adding model 'RatingComparator'
        db.create_table('core_ratingcomparator', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('main_user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='main_users', to=orm['auth.User'])),
            ('compared_user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='compared_users', to=orm['auth.User'])),
            ('comment', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('score', self.gf('django.db.models.fields.DecimalField')(max_digits=4, decimal_places=2)),
            ('score2', self.gf('django.db.models.fields.DecimalField')(default='0.00', max_digits=4, decimal_places=2)),
            ('common_films', self.gf('django.db.models.fields.IntegerField')()),
            ('sum_difference', self.gf('django.db.models.fields.IntegerField')()),
            ('previous_save_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('core', ['RatingComparator'])

        # Adding model 'FilmComparator'
        db.create_table('core_filmcomparator', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('main_film', self.gf('django.db.models.fields.related.ForeignKey')(related_name='main_films', to=orm['core.Film'])),
            ('compared_film', self.gf('django.db.models.fields.related.ForeignKey')(related_name='compared_films', to=orm['core.Film'])),
            ('score', self.gf('django.db.models.fields.DecimalField')(default='0.000', max_digits=5, decimal_places=3)),
        ))
        db.send_create_signal('core', ['FilmComparator'])

        # Adding model 'Recommendation'
        db.create_table('core_recommendation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('guess_rating_alg1', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=6, decimal_places=4, blank=True)),
            ('guess_rating_alg2', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=6, decimal_places=4, blank=True)),
            ('film', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='film_recommendation', null=True, to=orm['core.Film'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
        ))
        db.send_create_signal('core', ['Recommendation'])

        # Adding model 'FilmLog'
        db.create_table('core_filmlog', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
            ('version_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('LANG', self.gf('django.db.models.fields.CharField')(default='en', max_length=2)),
            ('saved_by', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('comment', self.gf('django.db.models.fields.CharField')(max_length=40000, null=True, blank=True)),
            ('type', self.gf('django.db.models.fields.IntegerField')()),
            ('film', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Film'])),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('release_year', self.gf('django.db.models.fields.IntegerField')()),
            ('release_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('tag_list', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('localized_title', self.gf('django.db.models.fields.CharField')(max_length=128)),
        ))
        db.send_create_signal('core', ['FilmLog'])

        # Adding model 'PersonLog'
        db.create_table('core_personlog', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
            ('version_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('LANG', self.gf('django.db.models.fields.CharField')(default='en', max_length=2)),
            ('saved_by', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('comment', self.gf('django.db.models.fields.CharField')(max_length=40000, null=True, blank=True)),
            ('type', self.gf('django.db.models.fields.IntegerField')()),
            ('person', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Person'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('surname', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('day_of_birth', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('month_of_birth', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('year_of_birth', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('gender', self.gf('django.db.models.fields.CharField')(max_length=1, null=True, blank=True)),
            ('is_director', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_actor', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_writer', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('actor_popularity', self.gf('django.db.models.fields.IntegerField')()),
            ('director_popularity', self.gf('django.db.models.fields.IntegerField')()),
            ('writer_popularity', self.gf('django.db.models.fields.IntegerField')()),
            ('actor_popularity_month', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('director_popularity_month', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('writer_popularity_month', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('tag_list', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('core', ['PersonLog'])

        # Adding model 'DeferredTask'
        db.create_table('core_deferredtask', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('queue_name', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('data', self.gf('django.db.models.fields.TextField')()),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('eta', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('try_cnt', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('max_tries', self.gf('django.db.models.fields.IntegerField')(default=5)),
        ))
        db.send_create_signal('core', ['DeferredTask'])

        # Adding model 'UserRatingTimeRange'
        db.create_table('core_userratingtimerange', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('first_rated', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('last_rated', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('LANG', self.gf('django.db.models.fields.CharField')(default='en', max_length=2)),
        ))
        db.send_create_signal('core', ['UserRatingTimeRange'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'LocalizedProfile', fields ['user', 'LANG']
        db.delete_unique('core_localizedprofile', ['user_id', 'LANG'])

        # Deleting model 'Object'
        db.delete_table('core_object')

        # Deleting model 'LocalizedProfile'
        db.delete_table('core_localizedprofile')

        # Deleting model 'Profile'
        db.delete_table('core_profile')

        # Deleting model 'Person'
        db.delete_table('core_person')

        # Deleting model 'Country'
        db.delete_table('core_country')

        # Deleting model 'Film'
        db.delete_table('core_film')

        # Removing M2M table for field directors on 'Film'
        db.delete_table('core_film_directors')

        # Removing M2M table for field writers on 'Film'
        db.delete_table('core_film_writers')

        # Removing M2M table for field production_country on 'Film'
        db.delete_table('core_film_production_country')

        # Deleting model 'ObjectLocalized'
        db.delete_table('core_objectlocalized')

        # Deleting model 'SearchKey'
        db.delete_table('core_searchkey')

        # Deleting model 'FilmLocalized'
        db.delete_table('core_filmlocalized')

        # Deleting model 'ModeratedFilmLocalized'
        db.delete_table('core_moderatedfilmlocalized')

        # Deleting model 'PersonLocalized'
        db.delete_table('core_personlocalized')

        # Deleting model 'Character'
        db.delete_table('core_character')

        # Deleting model 'Rating'
        db.delete_table('core_rating')

        # Deleting model 'FilmRanking'
        db.delete_table('core_filmranking')

        # Deleting model 'ShortReview'
        db.delete_table('core_shortreview')

        # Deleting model 'ShortReviewOld'
        db.delete_table('core_shortreviewold')

        # Deleting model 'RatingComparator'
        db.delete_table('core_ratingcomparator')

        # Deleting model 'FilmComparator'
        db.delete_table('core_filmcomparator')

        # Deleting model 'Recommendation'
        db.delete_table('core_recommendation')

        # Deleting model 'FilmLog'
        db.delete_table('core_filmlog')

        # Deleting model 'PersonLog'
        db.delete_table('core_personlog')

        # Deleting model 'DeferredTask'
        db.delete_table('core_deferredtask')

        # Deleting model 'UserRatingTimeRange'
        db.delete_table('core_userratingtimerange')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'followers': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'related_to'", 'symmetrical': 'False', 'through': "orm['followers.Followers']", 'to': "orm['auth.User']"}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'core.character': {
            'LANG': ('django.db.models.fields.CharField', [], {'default': "'en'", 'max_length': '2'}),
            'Meta': {'object_name': 'Character'},
            'character': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'description_full': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'null': 'True', 'blank': 'True'}),
            'description_lead': ('django.db.models.fields.CharField', [], {'max_length': '350', 'null': 'True', 'blank': 'True'}),
            'film': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Film']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'image_thumb': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'image_thumb_lost': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'importance': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Person']"})
        },
        'core.country': {
            'Meta': {'object_name': 'Country'},
            'country': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'core.deferredtask': {
            'Meta': {'object_name': 'DeferredTask'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'data': ('django.db.models.fields.TextField', [], {}),
            'eta': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_tries': ('django.db.models.fields.IntegerField', [], {'default': '5'}),
            'queue_name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'try_cnt': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'core.film': {
            'Meta': {'object_name': 'Film'},
            'actors': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'films_played'", 'to': "orm['core.Person']", 'through': "orm['core.Character']", 'blank': 'True', 'symmetrical': 'False', 'null': 'True'}),
            'criticker_id': ('django.db.models.fields.CharField', [], {'max_length': '16', 'null': 'True', 'blank': 'True'}),
            'directors': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'films_directed'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['core.Person']"}),
            'hires_image': ('django.db.models.fields.files.ImageField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'imdb_code': ('django.db.models.fields.CharField', [], {'max_length': '128', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'is_enh9': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'parent': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['core.Object']", 'unique': 'True', 'primary_key': 'True'}),
            'popularity': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'popularity_month': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'production_country': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'produced_in'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['core.Country']"}),
            'production_country_list': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'release_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'release_year': ('django.db.models.fields.IntegerField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'title_normalized': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'tmdb_import_status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'verified_imdb_code': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'writers': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'screenplays_written'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['core.Person']"})
        },
        'core.filmcomparator': {
            'Meta': {'object_name': 'FilmComparator'},
            'compared_film': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'compared_films'", 'to': "orm['core.Film']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'main_film': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'main_films'", 'to': "orm['core.Film']"}),
            'score': ('django.db.models.fields.DecimalField', [], {'default': "'0.000'", 'max_digits': '5', 'decimal_places': '3'})
        },
        'core.filmlocalized': {
            'Meta': {'object_name': 'FilmLocalized', '_ormbases': ['core.ObjectLocalized']},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '15000', 'null': 'True', 'blank': 'True'}),
            'fetched_description': ('django.db.models.fields.CharField', [], {'max_length': '15000', 'null': 'True', 'blank': 'True'}),
            'fetched_description_type': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'fetched_description_url': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'fetched_description_url_text': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'film': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Film']"}),
            'object_localized': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['core.ObjectLocalized']", 'unique': 'True', 'primary_key': 'True'}),
            'release_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'release_year': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'title_normalized': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'core.filmlog': {
            'LANG': ('django.db.models.fields.CharField', [], {'default': "'en'", 'max_length': '2'}),
            'Meta': {'object_name': 'FilmLog'},
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '40000', 'null': 'True', 'blank': 'True'}),
            'film': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Film']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'localized_title': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'release_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'release_year': ('django.db.models.fields.IntegerField', [], {}),
            'saved_by': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'tag_list': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'type': ('django.db.models.fields.IntegerField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'version_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'core.filmranking': {
            'Meta': {'object_name': 'FilmRanking'},
            'average_score': ('django.db.models.fields.DecimalField', [], {'max_digits': '4', 'decimal_places': '2'}),
            'film': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Film']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number_of_votes': ('django.db.models.fields.IntegerField', [], {}),
            'type': ('django.db.models.fields.IntegerField', [], {})
        },
        'core.localizedprofile': {
            'LANG': ('django.db.models.fields.CharField', [], {'default': "'en'", 'max_length': '2'}),
            'Meta': {'unique_together': "(('user', 'LANG'),)", 'object_name': 'LocalizedProfile'},
            'blog_title': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'core.moderatedfilmlocalized': {
            'LANG': ('django.db.models.fields.CharField', [], {'default': "'en'", 'max_length': '2'}),
            'Meta': {'object_name': 'ModeratedFilmLocalized'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '15000', 'null': 'True', 'blank': 'True'}),
            'film': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Film']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'moderation_status': ('django.db.models.fields.IntegerField', [], {'default': '-1'}),
            'moderation_status_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'moderation_status_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'moderatedfilmlocalized_moderated_objects'", 'null': 'True', 'to': "orm['auth.User']"}),
            'rejection_reason': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'tag_list': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'core.object': {
            'Meta': {'object_name': 'Object'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number_of_comments': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'permalink': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'type': ('django.db.models.fields.IntegerField', [], {}),
            'version': ('django.db.models.fields.IntegerField', [], {})
        },
        'core.objectlocalized': {
            'LANG': ('django.db.models.fields.CharField', [], {'default': "'en'", 'max_length': '2'}),
            'Meta': {'object_name': 'ObjectLocalized'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Object']"}),
            'tag_list': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'core.person': {
            'Meta': {'ordering': "['surname']", 'object_name': 'Person'},
            'actor_popularity': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'actor_popularity_month': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'day_of_birth': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'director_popularity': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'director_popularity_month': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'hires_image': ('django.db.models.fields.files.ImageField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'imdb_code': ('django.db.models.fields.CharField', [], {'max_length': '128', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'is_actor': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_director': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_writer': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'month_of_birth': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'parent': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['core.Object']", 'unique': 'True', 'primary_key': 'True'}),
            'surname': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'tmdb_import_status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'verified_imdb_code': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'writer_popularity': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'writer_popularity_month': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'year_of_birth': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'core.personlocalized': {
            'Meta': {'object_name': 'PersonLocalized', '_ormbases': ['core.ObjectLocalized']},
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'object_localized': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['core.ObjectLocalized']", 'unique': 'True', 'primary_key': 'True'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Person']"}),
            'surname': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'core.personlog': {
            'LANG': ('django.db.models.fields.CharField', [], {'default': "'en'", 'max_length': '2'}),
            'Meta': {'object_name': 'PersonLog'},
            'actor_popularity': ('django.db.models.fields.IntegerField', [], {}),
            'actor_popularity_month': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '40000', 'null': 'True', 'blank': 'True'}),
            'day_of_birth': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'director_popularity': ('django.db.models.fields.IntegerField', [], {}),
            'director_popularity_month': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_actor': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_director': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_writer': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'month_of_birth': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Person']"}),
            'saved_by': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'surname': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'tag_list': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'type': ('django.db.models.fields.IntegerField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'version_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'writer_popularity': ('django.db.models.fields.IntegerField', [], {}),
            'writer_popularity_month': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'year_of_birth': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'core.profile': {
            'LANG': ('django.db.models.fields.CharField', [], {'default': "'en'", 'max_length': '2'}),
            'Meta': {'object_name': 'Profile'},
            'aol': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'country': ('film20.userprofile.countries.CountryField', [], {'max_length': '2', 'null': 'True', 'blank': 'True'}),
            'criticker_name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'facebook_name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'foursquare_access_token': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'foursquare_user_id': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'gg': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'icq': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'imdb_name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'iphone_token': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'jabber_id': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'latitude': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '6', 'blank': 'True'}),
            'location': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'longitude': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '6', 'blank': 'True'}),
            'metacritic_name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'mobile_first_login_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'mobile_last_login_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'mobile_login_cnt': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'mobile_platform': ('django.db.models.fields.CharField', [], {'max_length': '16', 'null': 'True', 'blank': 'True'}),
            'msn': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'myspace_name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'recommendations_notice_sent': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'recommendations_status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'registration_source': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'timezone_id': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'twitter_access_token': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'twitter_user_id': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True'}),
            'website': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        'core.rating': {
            'Meta': {'object_name': 'Rating'},
            'actor': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'rated_as_actor'", 'null': 'True', 'to': "orm['core.Person']"}),
            'director': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'rated_as_director'", 'null': 'True', 'to': "orm['core.Person']"}),
            'film': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'film_ratings'", 'null': 'True', 'to': "orm['core.Film']"}),
            'first_rated': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'guess_rating_alg1': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '4', 'blank': 'True'}),
            'guess_rating_alg2': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '4', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_displayed': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'last_rated': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'normalized': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '4', 'blank': 'True'}),
            'number_of_comments': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'number_of_ratings': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Object']"}),
            'rating': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.IntegerField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'core.ratingcomparator': {
            'Meta': {'object_name': 'RatingComparator'},
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'common_films': ('django.db.models.fields.IntegerField', [], {}),
            'compared_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'compared_users'", 'to': "orm['auth.User']"}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'main_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'main_users'", 'to': "orm['auth.User']"}),
            'previous_save_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'score': ('django.db.models.fields.DecimalField', [], {'max_digits': '4', 'decimal_places': '2'}),
            'score2': ('django.db.models.fields.DecimalField', [], {'default': "'0.00'", 'max_digits': '4', 'decimal_places': '2'}),
            'sum_difference': ('django.db.models.fields.IntegerField', [], {}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'core.recommendation': {
            'Meta': {'object_name': 'Recommendation'},
            'film': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'film_recommendation'", 'null': 'True', 'to': "orm['core.Film']"}),
            'guess_rating_alg1': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '4', 'blank': 'True'}),
            'guess_rating_alg2': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '4', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'core.searchkey': {
            'Meta': {'object_name': 'SearchKey'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key_letters': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'key_normalized': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'key_root': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'object': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Object']"}),
            'object_localized': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ObjectLocalized']", 'null': 'True', 'blank': 'True'}),
            'text_length': ('django.db.models.fields.IntegerField', [], {})
        },
        'core.shortreview': {
            'LANG': ('django.db.models.fields.CharField', [], {'default': "'en'", 'max_length': '2'}),
            'Meta': {'object_name': 'ShortReview', '_ormbases': ['core.Object']},
            'created_at': ('django.db.models.fields.DateTimeField', [], {}),
            'kind': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'object': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'short_reviews'", 'null': 'True', 'to': "orm['core.Object']"}),
            'parent': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['core.Object']", 'unique': 'True', 'primary_key': 'True'}),
            'rating': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'short_reviews'", 'null': 'True', 'to': "orm['core.Rating']"}),
            'review_text': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'core.shortreviewold': {
            'LANG': ('django.db.models.fields.CharField', [], {'default': "'en'", 'max_length': '2'}),
            'Meta': {'object_name': 'ShortReviewOld'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'rating': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'short_reviewsold'", 'to': "orm['core.Rating']"}),
            'review_text': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'core.userratingtimerange': {
            'LANG': ('django.db.models.fields.CharField', [], {'default': "'en'", 'max_length': '2'}),
            'Meta': {'object_name': 'UserRatingTimeRange'},
            'first_rated': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_rated': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'followers.followers': {
            'Meta': {'ordering': "('-created_at',)", 'unique_together': "(('from_user', 'to_user', 'status'),)", 'object_name': 'Followers'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'from_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'from_users'", 'to': "orm['auth.User']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'to_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'to_users'", 'to': "orm['auth.User']"})
        },
        'tagging.tag': {
            'LANG': ('django.db.models.fields.CharField', [], {'default': "'en'", 'max_length': '2'}),
            'Meta': {'ordering': "('name',)", 'object_name': 'Tag'},
            'category': ('django.db.models.fields.IntegerField', [], {'default': '2'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'weight': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'tagging.taggeditem': {
            'Meta': {'unique_together': "(('tag', 'content_type', 'object_id'),)", 'object_name': 'TaggedItem'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'items'", 'to': "orm['tagging.Tag']"})
        }
    }

    complete_apps = ['core']
