from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def multiply(value, arg):
    return float(value) * float(arg)

@register.filter
def display_decimal(value):
    if isinstance(value, Decimal):
        if value == value.to_integral_value():
            return '{:.2f}'.format(value)
        else:
            return '{:.10f}'.format(value).rstrip('0').rstrip('.')
    return value