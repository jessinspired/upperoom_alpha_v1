from django import template
from listings.models import RoomProfile

register = template.Library()


@register.filter(name='count_vacancy')
def count_vacancy(creator):
    """Counts available vacancies for creator"""
    return RoomProfile.objects.filter(
        lodge__creator=creator,
        is_vacant=True
    ).count()
