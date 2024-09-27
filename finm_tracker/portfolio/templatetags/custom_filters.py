from django import template
from decimal import Decimal
from django.utils.safestring import mark_safe

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

@register.filter(is_safe=True)
def profit_loss_color(value):
    color = '#059669' if value >= 0 else '#e11d48'
    return mark_safe(f'style="color: {color};"')