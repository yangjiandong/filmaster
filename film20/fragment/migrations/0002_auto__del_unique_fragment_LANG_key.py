# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Removing unique constraint on 'Fragment', fields ['LANG', 'key']
        db.delete_unique('fragment_fragment', ['LANG', 'key'])


    def backwards(self, orm):
        
        # Adding unique constraint on 'Fragment', fields ['LANG', 'key']
        db.create_unique('fragment_fragment', ['LANG', 'key'])


    models = {
        'fragment.fragment': {
            'LANG': ('django.db.models.fields.CharField', [], {'default': "'en'", 'max_length': '2'}),
            'Meta': {'object_name': 'Fragment'},
            'body': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.SlugField', [], {'max_length': '150', 'db_index': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '150'})
        }
    }

    complete_apps = ['fragment']
