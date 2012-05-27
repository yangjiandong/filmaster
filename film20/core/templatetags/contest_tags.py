from django import template

import film20.settings as settings
FULL_DOMAIN = getattr(settings, "FULL_DOMAIN", "http://filmaster.pl")

register = template.Library()

@register.simple_tag
def winner_link(the_game, character):
    """
       Returns winner css class if given character is a winner or loser if lost the game
    """
    try:
        if the_game.winner.id == character.id:
            return "winner"
        else:
            return "looser"
    except:
        return ""

@register.simple_tag
def winner_ladder(the_game, character):
    """
       Retruns played first css class if first user won the game and played second if second won
    """
    try:
        if the_game.winner.id == character.id:
            return "played first"
        else:
            return "played second"
    except:
        return ""

@register.simple_tag
def character_thumb(the_game, character):
    """
        Returns color thumb if character is a winner or if the game is still on else returns black
       and white thumb, or return nothing if there is no thumb (this should not happen!)
    """
    try:
        if the_game.winner:
            if the_game.winner.id == character.id:
                return FULL_DOMAIN + character.image_thumb.url
            else:
                return FULL_DOMAIN + character.image_thumb_lost.url
        else:
            return FULL_DOMAIN + character.image_thumb.url
    except:
        return ""

@register.simple_tag
def character_image(character):
    """
       Returns large image for character in game
    """
    try:
        return FULL_DOMAIN + character.image.url
    except:
        return ""
