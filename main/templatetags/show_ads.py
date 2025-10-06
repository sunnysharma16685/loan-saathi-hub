from django import template
from main.models import PageAd

register = template.Library()

@register.inclusion_tag("partials/render_ads.html", takes_context=True)
def show_ads(context, position, page=None):
    """
    Usage in template:
    {% show_ads "left" %}
    {% show_ads "right" "loan_request" %}
    """
    qs = PageAd.objects.filter(position=position, is_active=True)
    if page:
        qs = qs.filter(page=page)

    return {"ads": qs, "position": position}
