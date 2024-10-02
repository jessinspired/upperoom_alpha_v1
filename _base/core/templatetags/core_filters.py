from django import template

register = template.Library()


@register.filter(name='capitalize')
def capitalize(text):
    """Capitalizes the first letter of the string"""
    if isinstance(text, str):
        return text.capitalize()
    return text


@register.filter(name='get_initials_in_uppercase')
def get_initials_in_uppercase(user):
    return f'{user.first_name[0].upper()}{user.last_name[0].upper()}'
