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


@register.filter
def mul(value, arg):
    """Multiply the value by the argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def div(value, arg):
    """Divide the value by the argument"""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0


@register.filter
def add(value, arg):
    """Add the argument to the value"""
    try:
        return float(value) + float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def make_range(value):
    """Create a range from 0 to value"""
    try:
        return range(int(value))
    except (ValueError, TypeError):
        return range(0)