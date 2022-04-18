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
    cart = json.loads(request.session.get("json_cart2", "{}"))
    return len(cart)


@register.simple_tag
def get_diff(total, stock):
    if stock is None or total is None:
        stock = total = 0
    return total - stock if total - stock > 0 else 0


@register.filter
def sort_keys(dict_to_sort):
    return sorted(dict_to_sort)


@register.simple_tag
def get_size_stock(sizes_dict, key):
    try:
        return sizes_dict[0].get(key, 0)
    except KeyError:
        return 0


@register.simple_tag
def url_replace(request, field, value):
    dict_ = request.GET.copy()
    dict_[field] = value
    return dict_.urlencode()


@register.filter(name="format")
def format_value(value, fmt):
    return fmt.format(value)
