from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary safely."""
    return dictionary.get(key) if dictionary else None
