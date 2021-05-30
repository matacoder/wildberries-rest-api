import json

from django import template

register = template.Library()


@register.simple_tag
def get_image_url(wb_id):
    base_url = "https://images.wbstatic.net/big/new/"
    end_url = "-1.jpg"
    wb_id_with_nulls = str(wb_id)[:-4] + "0000/"
    return base_url + wb_id_with_nulls + str(wb_id) + end_url


@register.simple_tag
def get_cart(request):
    cart = json.loads(request.session.get("json_cart", '{}'))
    return len(cart)


@register.simple_tag
def get_diff(total, stock):
    return total - stock if total - stock > 0 else 0
