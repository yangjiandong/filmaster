# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Tag'
        db.create_table('tagging_tag', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50, db_index=True)),
            ('weight', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('category', self.gf('django.db.models.fields.IntegerField')(default=2)),
            ('LANG', self.gf('django.db.models.fields.CharField')(default='en', max_length=2)),
        ))
        db.send_create_signal('tagging', ['Tag'])

        # Adding model 'TagAlias'
        db.create_table('tagging_tagalias', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50, db_index=True)),
            ('tag', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tagging.Tag'])),
        ))
        db.send_create_signal('tagging', ['TagAlias'])

        # Adding model 'TaggedItem'
        db.create_table('tagging_taggeditem', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('tag', self.gf('django.db.models.fields.related.ForeignKey')(related_name='items', to=orm['tagging.Tag'])),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
        ))
        db.send_create_signal('tagging', ['TaggedItem'])

        # Adding unique constraint on 'TaggedItem', fields ['tag', 'content_type', 'object_id']
        db.create_unique('tagging_taggeditem', ['tag_id', 'content_type_id', 'object_id'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'TaggedItem', fields ['tag', 'content_type', 'object_id']
        db.delete_unique('tagging_taggeditem', ['tag_id', 'content_type_id', 'object_id'])

        # Deleting model 'Tag'
        db.delete_table('tagging_tag')

        # Deleting model 'TagAlias'
        db.delete_table('tagging_tagalias')

        # Deleting model 'TaggedItem'
        db.delete_table('tagging_taggeditem')


    models = {
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'tagging.tag': {
            'LANG': ('django.db.models.fields.CharField', [], {'default': "'en'", 'max_length': '2'}),
            'Meta': {'ordering': "('name',)", 'object_name': 'Tag'},
            'category': ('django.db.models.fields.IntegerField', [], {'default': '2'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'weight': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'tagging.tagalias': {
            'Meta': {'object_name': 'TagAlias'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tagging.Tag']"})
        },
        'tagging.taggeditem': {
            'Meta': {'unique_together': "(('tag', 'content_type', 'object_id'),)", 'object_name': 'TaggedItem'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'items'", 'to': "orm['tagging.Tag']"})
        }
    }

    complete_apps = ['tagging']
