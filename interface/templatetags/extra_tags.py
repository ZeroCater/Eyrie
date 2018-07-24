import markdown
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


@register.filter
def markdown(text):
    rendered = markdown.markdown(text)

    # Remove <code> blocks nested in <pre>
    rendered = rendered.replace('<pre><span></span><code>', '<pre>').replace('<pre><code>', '<pre>')
    rendered = rendered.replace('</code></pre>', '</pre>')

    # Hacky fix for [``]() escaping inner <code> block
    rendered = rendered.replace('&lt;code&gt;', '<code>').replace('&lt;/code&gt;', '</code>')

    return mark_safe(rendered)
