from django import template

from apps.core.pagination import get_page_window

register = template.Library()


@register.simple_tag
def pagination_window(page_obj, on_each_side=2):
    return get_page_window(page_obj, on_each_side=on_each_side)
