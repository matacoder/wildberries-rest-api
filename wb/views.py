import logging

from django.shortcuts import render
from wb.services import WarehouseRestClient


def index(request):
    wc = WarehouseRestClient()
    data = wc.get_data().json()
    data = sorted(data, key=lambda x: x["quantity"], reverse=True)
    logging.warning(data)
    return render(request, "index.html", {"data": data[:30]})
