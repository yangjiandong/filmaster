# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Country'
        db.create_table('showtimes_country', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('code', self.gf('django.db.models.fields.CharField')(unique=True, max_length=2)),
        ))
        db.send_create_signal('showtimes', ['Country'])

        # Adding model 'Town'
        db.create_table('showtimes_town', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('country', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['showtimes.Country'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('last_fetched', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('has_cinemas', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('timezone_id', self.gf('django.db.models.fields.CharField')(max_length=40, null=True, blank=True)),
        ))
        db.send_create_signal('showtimes', ['Town'])

        # Adding model 'Channel'
        db.create_table('showtimes_channel', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('type', self.gf('django.db.models.fields.IntegerField')()),
            ('name_normalized', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('last_screening_time', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('timezone_id', self.gf('django.db.models.fields.CharField')(max_length=40, null=True, blank=True)),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('is_default', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('icon', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True, blank=True)),
        ))
        db.send_create_signal('showtimes', ['Channel'])

        # Adding model 'Fetcher'
        db.create_table('showtimes_fetcher', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('channel', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['showtimes.Channel'])),
            ('cid', self.gf('django.db.models.fields.CharField')(max_length=128)),
        ))
        db.send_create_signal('showtimes', ['Fetcher'])

        # Adding unique constraint on 'Fetcher', fields ['name', 'channel']
        db.create_unique('showtimes_fetcher', ['name', 'channel_id'])

        # Adding unique constraint on 'Fetcher', fields ['name', 'cid']
        db.create_unique('showtimes_fetcher', ['name', 'cid'])

        # Adding model 'TVChannel'
        db.create_table('showtimes_tvchannel', (
            ('channel_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['showtimes.Channel'], unique=True, primary_key=True)),
            ('country', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['showtimes.Country'])),
        ))
        db.send_create_signal('showtimes', ['TVChannel'])

        # Adding model 'Cinema'
        db.create_table('showtimes_cinema', (
            ('channel_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['showtimes.Channel'], unique=True, primary_key=True)),
            ('town', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['showtimes.Town'])),
            ('address', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('latitude', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=10, decimal_places=6, blank=True)),
            ('longitude', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=10, decimal_places=6, blank=True)),
            ('fetcher1_id', self.gf('django.db.models.fields.CharField')(max_length=128)),
        ))
        db.send_create_signal('showtimes', ['Cinema'])

        # Adding model 'UserChannel'
        db.create_table('showtimes_userchannel', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('channel', self.gf('django.db.models.fields.related.ForeignKey')(related_name='userchannel', to=orm['showtimes.Channel'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('distance', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=5, decimal_places=1, blank=True)),
        ))
        db.send_create_signal('showtimes', ['UserChannel'])

        # Adding model 'QueuedLocation'
        db.create_table('showtimes_queuedlocation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('latitude', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=10, decimal_places=6, blank=True)),
            ('longitude', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=10, decimal_places=6, blank=True)),
            ('status', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('town', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['showtimes.Town'], null=True, blank=True)),
        ))
        db.send_create_signal('showtimes', ['QueuedLocation'])

        # Adding model 'FilmOnChannel'
        db.create_table('showtimes_filmonchannel', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('localized_title', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('info', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('year', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('directors', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('imdb_code', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('film', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Film'], null=True, blank=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('match', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('source', self.gf('django.db.models.fields.CharField')(max_length=32, blank=True)),
        ))
        db.send_create_signal('showtimes', ['FilmOnChannel'])

        # Adding M2M table for field candidates on 'FilmOnChannel'
        db.create_table('showtimes_filmonchannel_candidates', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('filmonchannel', models.ForeignKey(orm['showtimes.filmonchannel'], null=False)),
            ('film', models.ForeignKey(orm['core.film'], null=False))
        ))
        db.create_unique('showtimes_filmonchannel_candidates', ['filmonchannel_id', 'film_id'])

        # Adding model 'Screening'
        db.create_table('showtimes_screening', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('channel', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['showtimes.Channel'])),
            ('film', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['showtimes.FilmOnChannel'])),
            ('utc_time', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('info', self.gf('django.db.models.fields.CharField')(max_length=64, null=True, blank=True)),
        ))
        db.send_create_signal('showtimes', ['Screening'])

        # Adding unique constraint on 'Screening', fields ['channel', 'film', 'utc_time']
        db.create_unique('showtimes_screening', ['channel_id', 'film_id', 'utc_time'])

        # Adding model 'ScreeningCheckIn'
        db.create_table('showtimes_screeningcheckin', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('screening', self.gf('django.db.models.fields.related.ForeignKey')(related_name='checkins', null=True, to=orm['showtimes.Screening'])),
            ('film', self.gf('django.db.models.fields.related.ForeignKey')(related_name='film_checkins', null=True, to=orm['core.Film'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('status', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('number_of_comments', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('showtimes', ['ScreeningCheckIn'])

        # Adding unique constraint on 'ScreeningCheckIn', fields ['screening', 'user']
        db.create_unique('showtimes_screeningcheckin', ['screening_id', 'user_id'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'ScreeningCheckIn', fields ['screening', 'user']
        db.delete_unique('showtimes_screeningcheckin', ['screening_id', 'user_id'])

        # Removing unique constraint on 'Screening', fields ['channel', 'film', 'utc_time']
        db.delete_unique('showtimes_screening', ['channel_id', 'film_id', 'utc_time'])

        # Removing unique constraint on 'Fetcher', fields ['name', 'cid']
        db.delete_unique('showtimes_fetcher', ['name', 'cid'])

        # Removing unique constraint on 'Fetcher', fields ['name', 'channel']
        db.delete_unique('showtimes_fetcher', ['name', 'channel_id'])

        # Deleting model 'Country'
        db.delete_table('showtimes_country')

        # Deleting model 'Town'
        db.delete_table('showtimes_town')

        # Deleting model 'Channel'
        db.delete_table('showtimes_channel')

        # Deleting model 'Fetcher'
        db.delete_table('showtimes_fetcher')

        # Deleting model 'TVChannel'
        db.delete_table('showtimes_tvchannel')

        # Deleting model 'Cinema'
        db.delete_table('showtimes_cinema')

        # Deleting model 'UserChannel'
        db.delete_table('showtimes_userchannel')

        # Deleting model 'QueuedLocation'
        db.delete_table('showtimes_queuedlocation')

        # Deleting model 'FilmOnChannel'
        db.delete_table('showtimes_filmonchannel')

        # Removing M2M table for field candidates on 'FilmOnChannel'
        db.delete_table('showtimes_filmonchannel_candidates')

        # Deleting model 'Screening'
        db.delete_table('showtimes_screening')

        # Deleting model 'ScreeningCheckIn'
        db.delete_table('showtimes_screeningcheckin')


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
        'core.object': {
            'Meta': {'object_name': 'Object'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number_of_comments': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'permalink': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'type': ('django.db.models.fields.IntegerField', [], {}),
            'version': ('django.db.models.fields.IntegerField', [], {})
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
        'followers.followers': {
            'Meta': {'ordering': "('-created_at',)", 'unique_together': "(('from_user', 'to_user', 'status'),)", 'object_name': 'Followers'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'from_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'from_users'", 'to': "orm['auth.User']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'to_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'to_users'", 'to': "orm['auth.User']"})
        },
        'showtimes.channel': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Channel'},
            'icon': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_default': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_screening_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'name_normalized': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'selected_by': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "u'selected_channels'", 'symmetrical': 'False', 'through': "orm['showtimes.UserChannel']", 'to': "orm['auth.User']"}),
            'timezone_id': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.IntegerField', [], {})
        },
        'showtimes.cinema': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Cinema', '_ormbases': ['showtimes.Channel']},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'channel_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['showtimes.Channel']", 'unique': 'True', 'primary_key': 'True'}),
            'fetcher1_id': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'latitude': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '6', 'blank': 'True'}),
            'longitude': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '6', 'blank': 'True'}),
            'town': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['showtimes.Town']"})
        },
        'showtimes.country': {
            'Meta': {'object_name': 'Country'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '2'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '32'})
        },
        'showtimes.fetcher': {
            'Meta': {'unique_together': "(('name', 'channel'), ('name', 'cid'))", 'object_name': 'Fetcher'},
            'channel': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['showtimes.Channel']"}),
            'cid': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '32'})
        },
        'showtimes.filmonchannel': {
            'Meta': {'object_name': 'FilmOnChannel'},
            'candidates': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'cinema_candidate'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['core.Film']"}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'directors': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'film': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Film']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'imdb_code': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'info': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'localized_title': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'match': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'year': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'showtimes.queuedlocation': {
            'Meta': {'object_name': 'QueuedLocation'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latitude': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '6', 'blank': 'True'}),
            'longitude': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '6', 'blank': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'town': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['showtimes.Town']", 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'showtimes.screening': {
            'Meta': {'unique_together': "(('channel', 'film', 'utc_time'),)", 'object_name': 'Screening'},
            'channel': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['showtimes.Channel']"}),
            'film': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['showtimes.FilmOnChannel']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'info': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'utc_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        'showtimes.screeningcheckin': {
            'Meta': {'unique_together': "(('screening', 'user'),)", 'object_name': 'ScreeningCheckIn'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'film': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'film_checkins'", 'null': 'True', 'to': "orm['core.Film']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'number_of_comments': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'screening': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'checkins'", 'null': 'True', 'to': "orm['showtimes.Screening']"}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'showtimes.town': {
            'Meta': {'object_name': 'Town'},
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['showtimes.Country']"}),
            'has_cinemas': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_fetched': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'timezone_id': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'})
        },
        'showtimes.tvchannel': {
            'Meta': {'ordering': "('country', 'name')", 'object_name': 'TVChannel', '_ormbases': ['showtimes.Channel']},
            'channel_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['showtimes.Channel']", 'unique': 'True', 'primary_key': 'True'}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['showtimes.Country']"})
        },
        'showtimes.userchannel': {
            'Meta': {'object_name': 'UserChannel'},
            'channel': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'userchannel'", 'to': "orm['showtimes.Channel']"}),
            'distance': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '5', 'decimal_places': '1', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        }
    }

    complete_apps = ['showtimes']
