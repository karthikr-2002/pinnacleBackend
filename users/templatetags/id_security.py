from django import template
from users.id_encryption import encode_id

register = template.Library()


@register.filter(name='eid')
def eid_filter(value):
    """Template filter to encode integer ID into an encrypted token: {{ obj.id|eid }}"""
    if not value:
        return ''
    return encode_id(value)

