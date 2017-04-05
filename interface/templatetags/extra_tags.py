from django import template
from django.utils.safestring import mark_safe


register = template.Library()


@register.filter
def humanize_td(delta):
    d = delta.days
    h, s = divmod(delta.seconds, 3600)
    m, s = divmod(s, 60)
    labels = ['d', 'h', 'm', 's']
    dhms = ['%s%s' % (i, lbl) for i, lbl in zip([d, h, m, s], labels)]
    for start in range(len(dhms)):
        if not dhms[start].startswith('0'):
            break
    for end in range(len(dhms)-1, -1, -1):
        if not dhms[end].startswith('0'):
            break
    return mark_safe(', '.join(dhms[start:end+1]))
