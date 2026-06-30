from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Template filter to get an item from a dictionary.
    Usage: {{ dictionary|get_item:key }}
    """
    if not dictionary:
        return None
        
    # Try getting exactly as the key was passed
    value = dictionary.get(key)
    
    # If not found and key is a string digit, try as integer
    if value is None and isinstance(key, str) and key.isdigit():
        value = dictionary.get(int(key))
        
    return value
