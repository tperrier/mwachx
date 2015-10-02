from django import template
import re

register = template.Library()

@register.filter()
def form_controller(value):
    words = re.split('\W+',value)
    return ''.join(word.capitalize() for word in words[:-1]) + 'Controller'

@register.filter()
def camel(value):
    words = re.split('\W+',value)
    return words[0] + ''.join(word.capitalize() for word  in words[1:])
