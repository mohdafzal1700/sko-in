from django import template

register = template.Library()

@register.filter(name='range')
def range_filter(number):
    if number is None:
        return range(0)  
    return range(int(number))