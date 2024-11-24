from django import template
from decimal import Decimal
from django.utils.safestring import mark_safe

# Register the template library for custom filters
register = template.Library()

@register.filter
def multiply(value, arg):
    """
    Custom filter to multiply two numbers.
    Usage in template: {{ value|multiply:arg }}
    Example: {{ price|multiply:quantity }}
    """
    return float(value) * float(arg)

@register.filter
def display_decimal(value):
    """
    Format decimal numbers with appropriate precision:
    - For whole numbers: display with 2 decimal places (e.g., 100.00)
    - For fractional numbers: display up to 10 decimal places, removing trailing zeros
    
    Usage in template: {{ value|display_decimal }}
    Example: 100.00000 becomes 100; 100.10000 becomes 100.1
    """
    if isinstance(value, Decimal):
        if value == value.to_integral_value():
            return '{:.2f}'.format(value)
        else:
            return '{:.10f}'.format(value).rstrip('0').rstrip('.')
    return value

@register.filter(is_safe=True)
def profit_loss_color(value):
    """
    Apply color styling based on profit/loss value:
    - Green (#059669) for positive values (profits)
    - Red (#e11d48) for negative values (losses)
    
    Usage in template: {{ value|profit_loss_color }}
    Example: <span {{ profit_value|profit_loss_color }}>{{ profit_value }}</span>
    """
    color = '#059669' if value >= 0 else '#e11d48'
    return mark_safe(f'style="color: {color};"')

@register.filter
def remove_usd_suffix(value):
    """
    Remove USD suffix from asset symbols.
    For example: 'BTC-USD' becomes 'BTC'
    
    Usage in template: {{ value|remove_usd_suffix }}
    Example: {{ asset_symbol|remove_usd_suffix }}
    """
    return value.split('-')[0] if '-' in value else value