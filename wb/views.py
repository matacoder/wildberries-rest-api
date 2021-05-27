import logging

from django.shortcuts import render
from wb.services import WarehouseRestClient
from django.core.paginator import Paginator


def index(request):
    wc = WarehouseRestClient()
    page_obj = {"supplierArticle": "Could not load"}
    try:
        data = wc.get_data().json()
        in_stock = filter(lambda x: x["quantity"] > 0, data)
        sorted_in_stock = sorted(in_stock, key=lambda x: x["quantity"], reverse=True)
        paginator = Paginator(sorted_in_stock, 32)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        logging.warning(e)
    return render(request, "index.html", {"data": page_obj})
