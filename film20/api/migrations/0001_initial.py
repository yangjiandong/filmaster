# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'SaaSUser'
        db.create_table('api_saasuser', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('username', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('password', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('user_prefix', self.gf('django.db.models.fields.CharField')(max_length=8)),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('api', ['SaaSUser'])


    def backwards(self, orm):
        
        # Deleting model 'SaaSUser'
        db.delete_table('api_saasuser')


    models = {
        'api.saasuser': {
            'Meta': {'object_name': 'SaaSUser'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'user_prefix': ('django.db.models.fields.CharField', [], {'max_length': '8'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '32'})
        }
    }

    complete_apps = ['api']
