import datetime
from django import template

register = template.Library()


@register.simple_tag
def get_image_url(wb_id):
    base_url = "https://images.wbstatic.net/big/new/"
    end_url = "-1.jpg"
    wb_id_with_nulls = str(wb_id)[:-4] + "0000/"
    return base_url + wb_id_with_nulls + str(wb_id) + end_url

