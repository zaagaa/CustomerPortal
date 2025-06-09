from django import template

register = template.Library()

@register.filter
def replace_underscore(value):
    return str(value).replace('_', ' ')


@register.filter
def intcomma_indian(value):
    try:
        value = float(value)
    except (ValueError, TypeError):
        return value

    is_negative = value < 0
    value = abs(value)

    number = str(int(value))
    if len(number) <= 3:
        result = number
    else:
        last3 = number[-3:]
        rest = number[:-3]
        rest_with_commas = ','.join(
            [rest[max(i - 2, 0):i] for i in range(len(rest), 0, -2)][::-1]
        )
        result = rest_with_commas + ',' + last3

    decimal_part = f"{value:.2f}".split('.')[-1]
    formatted = f"{result}.{decimal_part}"

    return f"-{formatted}" if is_negative else formatted
