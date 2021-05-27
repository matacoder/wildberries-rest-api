import logging

from django.shortcuts import render
from wb.services import RestClient
from django.core.paginator import Paginator


def index(request):
    client = RestClient()
    page_obj = []
    try:
        data = client.get_stock().json()
        in_stock = filter(lambda x: x["quantity"] > 0, data)
        sorted_in_stock = sorted(in_stock, key=lambda x: x["quantity"], reverse=True)
        paginator = Paginator(sorted_in_stock, 32)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        logging.warning(e)
    return render(request, "index.html", {"data": page_obj})


def stock(request):
    return index(request)


def ordered(request):
    client = RestClient()
    page_obj = []
    try:
        data = client.get_ordered().json()
        sorted_by_date = sorted(data, key=lambda x: x["date"], reverse=True)
        paginator = Paginator(sorted_by_date, 32)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        logging.warning(e)
    return render(request, "ordered.html", {"data": page_obj})


def bought(request):
    return None
