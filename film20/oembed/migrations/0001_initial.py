# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'ProviderRule'
        db.create_table('oembed_providerrule', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('regex', self.gf('django.db.models.fields.CharField')(max_length=2000)),
            ('endpoint', self.gf('django.db.models.fields.CharField')(max_length=2000)),
            ('format', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('oembed', ['ProviderRule'])

        # Adding model 'StoredOEmbed'
        db.create_table('oembed_storedoembed', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('match', self.gf('django.db.models.fields.TextField')()),
            ('max_width', self.gf('django.db.models.fields.IntegerField')()),
            ('max_height', self.gf('django.db.models.fields.IntegerField')()),
            ('html', self.gf('django.db.models.fields.TextField')()),
            ('date_added', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
        ))
        db.send_create_signal('oembed', ['StoredOEmbed'])


    def backwards(self, orm):
        
        # Deleting model 'ProviderRule'
        db.delete_table('oembed_providerrule')

        # Deleting model 'StoredOEmbed'
        db.delete_table('oembed_storedoembed')


    models = {
        'oembed.providerrule': {
            'Meta': {'object_name': 'ProviderRule'},
            'endpoint': ('django.db.models.fields.CharField', [], {'max_length': '2000'}),
            'format': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'regex': ('django.db.models.fields.CharField', [], {'max_length': '2000'})
        },
        'oembed.storedoembed': {
            'Meta': {'object_name': 'StoredOEmbed'},
            'date_added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'html': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'match': ('django.db.models.fields.TextField', [], {}),
            'max_height': ('django.db.models.fields.IntegerField', [], {}),
            'max_width': ('django.db.models.fields.IntegerField', [], {})
        }
    }

    complete_apps = ['oembed']
