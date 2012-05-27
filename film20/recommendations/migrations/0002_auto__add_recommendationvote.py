# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'RecommendationVote'
        db.create_table('recommendations_recommendationvote', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('film', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Film'])),
            ('average_rating', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=6, decimal_places=4)),
            ('number_of_ratings', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('ratings_based_prediction', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=6, decimal_places=4)),
            ('traits_based_prediction', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=6, decimal_places=4)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('vote', self.gf('django.db.models.fields.IntegerField')(default=0, null=True)),
        ))
        db.send_create_signal('recommendations', ['RecommendationVote'])


    def backwards(self, orm):
        
        # Deleting model 'RecommendationVote'
        db.delete_table('recommendations_recommendationvote')


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
            'LANG': ('django.db.models.fields.CharField', [], {'default': "'pl'", 'max_length': '2'}),
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
            'similar_films': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'similar_to'", 'symmetrical': 'False', 'through': "orm['core.SimilarFilm']", 'to': "orm['core.Film']"}),
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
            'import_comment': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
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
        'core.similarfilm': {
            'Meta': {'ordering': "('-number_of_votes',)", 'unique_together': "(('film_a', 'film_b'),)", 'object_name': 'SimilarFilm'},
            'film_a': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'similar_film_a'", 'to': "orm['core.Film']"}),
            'film_b': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'similar_film_b'", 'to': "orm['core.Film']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number_of_votes': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'votes': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'})
        },
        'followers.followers': {
            'Meta': {'ordering': "('-created_at',)", 'unique_together': "(('from_user', 'to_user', 'status'),)", 'object_name': 'Followers'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'from_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'from_users'", 'to': "orm['auth.User']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'to_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'to_users'", 'to': "orm['auth.User']"})
        },
        'recommendations.computed': {
            'Meta': {'object_name': 'Computed'},
            'comparators': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'recommendations': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'recommendations.recommendationvote': {
            'Meta': {'object_name': 'RecommendationVote'},
            'average_rating': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '4'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'film': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Film']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number_of_ratings': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'ratings_based_prediction': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '4'}),
            'traits_based_prediction': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '4'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'vote': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True'})
        }
    }

    complete_apps = ['recommendations']