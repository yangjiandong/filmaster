# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Item'
        db.create_table('shop_item', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('film', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Film'])),
            ('external_id', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('url_product', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('url_add_to_basket', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('url_image', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('LANG', self.gf('django.db.models.fields.CharField')(default='en', max_length=2)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('shop', ['Item'])


    def backwards(self, orm):
        
        # Deleting model 'Item'
        db.delete_table('shop_item')


    models = {
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
        'shop.item': {
            'LANG': ('django.db.models.fields.CharField', [], {'default': "'en'", 'max_length': '2'}),
            'Meta': {'object_name': 'Item'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'external_id': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'film': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Film']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'url_add_to_basket': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'url_image': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'url_product': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['shop']
