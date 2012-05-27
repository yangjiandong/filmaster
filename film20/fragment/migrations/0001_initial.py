# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Fragment'
        db.create_table('fragment_fragment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=150)),
            ('key', self.gf('django.db.models.fields.SlugField')(max_length=150, db_index=True)),
            ('body', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('LANG', self.gf('django.db.models.fields.CharField')(default='en', max_length=2)),
        ))
        db.send_create_signal('fragment', ['Fragment'])

        # Adding unique constraint on 'Fragment', fields ['key', 'LANG']
        db.create_unique('fragment_fragment', ['key', 'LANG'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'Fragment', fields ['key', 'LANG']
        db.delete_unique('fragment_fragment', ['key', 'LANG'])

        # Deleting model 'Fragment'
        db.delete_table('fragment_fragment')


    models = {
        'fragment.fragment': {
            'LANG': ('django.db.models.fields.CharField', [], {'default': "'en'", 'max_length': '2'}),
            'Meta': {'unique_together': "(('key', 'LANG'),)", 'object_name': 'Fragment'},
            'body': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.SlugField', [], {'max_length': '150', 'db_index': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '150'})
        }
    }

    complete_apps = ['fragment']
