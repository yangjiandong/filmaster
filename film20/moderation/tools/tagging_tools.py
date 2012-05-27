import json

from django import forms
from django.db.models import Q
from django.conf import settings
from django.db import transaction
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils.translation import gettext_lazy as _

from film20.moderation.tasks import rename_tag
from film20.core.models import ObjectLocalized
from film20.tagging.utils import parse_tag_input
from film20.moderation.registry import registry
from film20.moderation.items import ModeratorTool
from film20.tagging.models import Tag, TagAlias, TaggedItem, TagTranslation

def parse_tag( name ):
    parsed = parse_tag_input( name + ", " )
    if len( parsed ) != 1:
        raise forms.ValidationError( _( 'Provide one valid tag name' ) )
    return parsed[0]


class TagRenameForm( forms.Form ):
    tagA = forms.CharField( label=_( "the tag to be renamed" ) )
    tagB = forms.CharField( label=_( "new tag" ) )

    def clean_tagA( self ):
        name = parse_tag( self.cleaned_data['tagA'] )
        try:
            Tag.objects.get( name=name )
            return name
        except Tag.DoesNotExist:
            raise forms.ValidationError( _( 'Tag does not exists' ) )

    def clean_tagB( self ):
        return parse_tag( self.cleaned_data['tagB'] )

    def clean( self ):
        cleaned_data = self.cleaned_data
        tagA = cleaned_data.get( 'tagA' )
        tagB = cleaned_data.get( 'tagB' )

        if tagA is not None and tagB is not None and tagA == tagB:
            raise forms.ValidationError( _( "The tag A and tag B must be different " ) )

        return cleaned_data


class TagCreateAliasForm( forms.Form ):
    tag = forms.CharField( label=_( "the tag to set alias" ) )
    aliases = forms.CharField( label=_( "aliases" ) )

    def clean_tag( self ):
        name = parse_tag( self.cleaned_data['tag'] )
        try:
            return Tag.objects.get( name=name )
        except Tag.DoesNotExist:
            raise forms.ValidationError( _( 'Tag does not exists' ) )

    def clean_aliases( self ):
        aliases = parse_tag_input( self.cleaned_data['aliases'] )
        if len( aliases ) == 0:
            raise forms.ValidationError( _( 'You must enter at least one alias' ) )

        for alias in aliases:
            # alias cannot be existing tag
            if Tag.objects.filter( name=alias ).count() > 0:
                raise forms.ValidationError( _( 'Alias cannot be existing tag, first rename tag:' ) + "'%s'" % alias )

        return aliases
            

    def clean( self ):
        cleaned_data = self.cleaned_data
        tag = cleaned_data.get( 'tag' )
        aliases = cleaned_data.get( 'aliases' )

        # alias cannot be assignet to multiple tags
        for alias in aliases if aliases else []:
            tag_aliases = TagAlias.objects.filter( tag__LANG=settings.LANGUAGE_CODE, name=alias ).exclude( tag=tag )
            if tag_aliases.count() > 0:
                raise forms.ValidationError( _( 'Alias is already assigned to tag:' ) + "'%s'" % tag_aliases[0].tag )

        return cleaned_data


class TagTranslationForm( forms.Form ):
    f = forms.CharField( label=_( "tag to translate" ) )
    t = forms.CharField( label=_( "translation" ) )

    def clean_f( self ):
        return parse_tag( self.cleaned_data['f'] )

    def clean_t( self ):
        return parse_tag( self.cleaned_data['t'] )

#    def clean( self ):
#        cleaned_data = self.cleaned_data
#        f = cleaned_data.get( 'f' )
#        t = cleaned_data.get( 't' )
#        if t == f:
#            raise forms.ValidationError( _( '"tag to translate" and "translation" must be different' ) )
#        return cleaned_data


class TagRenamingTool( ModeratorTool ):
    name = "rename-tag"
    permission = "core.can_edit_tags"
    verbose_name = _( "Rename a tag" )

    def get_view( self, request ):
        moderated_items = registry.get_by_user( request.user )

        ctx = {
            "moderated_item": registry.get_by_name( self.name ),
            "moderated_items": moderated_items['items'],
            "moderator_tools": moderated_items['tools']
        }

        if request.method == 'POST':
            ctx['form'] = TagRenameForm( request.POST )
            if ctx['form'].is_valid():
                cleaned_data = ctx['form'].cleaned_data
                
                tag_a_name = cleaned_data['tagA']
                tag_a_tag = Tag.objects.get( name=tag_a_name )
                tag_a_count = self._get_tagged_objects_count( tag_a_tag )
                
                tag_b_name = cleaned_data['tagB']
                tag_b_tag = None
                try:
                    tag_b_tag = Tag.objects.get( name=tag_b_name )
                except Tag.DoesNotExist:
                    pass
                tag_b_count = self._get_tagged_objects_count( tag_b_tag ) if tag_b_tag else 0

                if not 'confirm' in request.POST:
                    ctx['to_confirm'] = {
                        'tagA': {
                            'name' : tag_a_name,
                            'count': tag_a_count,
                        },
                        'tagB': {
                            'name' : tag_b_name,
                            'count': tag_b_count,
                        }
                    }

                else:
                    
                    rename_tag.delay( tag_a_name, tag_b_name, request.user )
                    
                    messages.add_message( request, messages.INFO, _( "your task will be executed in the background, you will be informed when it's finished" ) )
                    return redirect( self.get_absolute_url() )

        else: 
            ctx['form'] = TagRenameForm()

        return render( request, 'moderation/rename_tag/create.html', ctx )

    def _get_tagged_objects_count( self, tag ):
        return TaggedItem.objects.filter( tag=tag ).count()

class TagAliasTool( ModeratorTool ):
    name = "alias-tag"
    permission = "core.can_edit_tags"
    verbose_name = _( "Create alias for tag" )

    def get_view( self, request ):
        moderated_items = registry.get_by_user( request.user )

        ctx = {
            "moderated_item": registry.get_by_name( self.name ),
            "moderated_items": moderated_items['items'],
            "moderator_tools": moderated_items['tools']
        }

        if request.method == 'POST':
            ctx['form'] = TagCreateAliasForm( request.POST )
            if ctx['form'].is_valid():
                cleaned_data = ctx['form'].cleaned_data
                
                tag = cleaned_data['tag']
                aliases = cleaned_data['aliases']

                already_added = TagAlias.objects.filter( tag=tag )
                for added in already_added:
                    if added.name in aliases:
                        aliases.remove( added.name )
                    else:
                        added.delete()
               
                for alias in aliases:
                    TagAlias.objects.create( tag=tag, name=alias )
                
                messages.add_message( request, messages.INFO, _( "Alias created!" ) )
                return redirect( self.get_absolute_url() )

        else: 
            ctx['form'] = TagCreateAliasForm()

        return render( request, 'moderation/tag_aliases/create.html', ctx )


class TagTranslateToolA( ModeratorTool ):
    name = "tag-translation-a"
    permission = "core.can_edit_tags"
    verbose_name = _( "Translate tag" )

    def get_view( self, request ):
        moderated_items = registry.get_by_user( request.user )

        ctx = {
            "moderated_item": registry.get_by_name( self.name ),
            "moderated_items": moderated_items['items'],
            "moderator_tools": moderated_items['tools']
        }

        if request.method == 'POST':
            ctx['form'] = TagTranslationForm( request.POST )
            if ctx['form'].is_valid():
                cleaned_data = ctx['form'].cleaned_data
                
                f = cleaned_data['f']
                t = cleaned_data['t']

                TagTranslation.create_translation( f, t )

                messages.add_message( request, messages.INFO, _( "Tag translated!" ) )
                return redirect( self.get_absolute_url() )

        else: 
            ctx['form'] = TagTranslationForm()

        return render( request, 'moderation/tag_translation/create.html', ctx )



class TagTranslateToolB( ModeratorTool ):
    name = "tag-translation-b"
    permission = "core.can_edit_tags"
    verbose_name = _( "Tags to translate" )

    def get_view( self, request ):
        moderated_items = registry.get_by_user( request.user )

        ctx = {
            "moderated_item": registry.get_by_name( self.name ),
            "moderated_items": moderated_items['items'],
            "moderator_tools": moderated_items['tools']
        }

        lang = settings.LANGUAGE_CODE
        to_lang = TagTranslation.to_lang()
        
        if request.method == 'POST':
            for f, t in request.POST.items():
                TagTranslation.create_translation( f, t )
        
            if request.is_ajax():
                return HttpResponse( json.dumps( { 'success': True  } ) )

        kwargs = {
            "%s__isnull" % to_lang: False
        }
        translated = [ t[lang] for t in TagTranslation.objects.filter( **kwargs ).values( lang ) ]
        ctx['items'] = Tag.objects.all().exclude( name__in=translated ).order_by( 'weight' )
        ctx['lang'] = lang
        ctx['to_lang'] = to_lang

        return render( request, 'moderation/tag_translation/list.html', ctx )


registry.register( TagAliasTool() )
registry.register( TagRenamingTool() )
registry.register( TagTranslateToolA() )
registry.register( TagTranslateToolB() )
