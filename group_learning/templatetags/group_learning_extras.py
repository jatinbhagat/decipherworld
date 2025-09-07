from django import template

register = template.Library()


@register.filter
def unique_players(player_actions):
    """Return unique players from a queryset of player actions"""
    return player_actions.values('player_name', 'player_session_id').distinct()


@register.filter
def split(value, separator):
    """Split a string by separator"""
    return value.split(separator)