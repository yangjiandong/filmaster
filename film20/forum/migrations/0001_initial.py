# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Forum'
        db.create_table('forum_forum', (
            ('parent', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['core.Object'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('forum', ['Forum'])

        # Adding model 'Thread'
        db.create_table('forum_thread', (
            ('parent', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['core.Object'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('forum', ['Thread'])


    def backwards(self, orm):
        
        # Deleting model 'Forum'
        db.delete_table('forum_forum')

        # Deleting model 'Thread'
        db.delete_table('forum_thread')


    models = {
        'core.object': {
            'Meta': {'object_name': 'Object'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number_of_comments': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'permalink': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'type': ('django.db.models.fields.IntegerField', [], {}),
            'version': ('django.db.models.fields.IntegerField', [], {})
        },
        'forum.forum': {
            'Meta': {'object_name': 'Forum', '_ormbases': ['core.Object']},
            'parent': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['core.Object']", 'unique': 'True', 'primary_key': 'True'})
        },
        'forum.thread': {
            'Meta': {'object_name': 'Thread', '_ormbases': ['core.Object']},
            'parent': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['core.Object']", 'unique': 'True', 'primary_key': 'True'})
        }
    }

    complete_apps = ['forum']
