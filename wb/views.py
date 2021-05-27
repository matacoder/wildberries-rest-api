import logging

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from wb.forms import ApiForm
from wb.services import RestClient
from django.core.paginator import Paginator


@login_required
def index(request):
    client = RestClient(user=request.user)
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


@login_required
def stock(request):
    return index(request)


@login_required
def ordered(request):
    client = RestClient(user=request.user)
    page_obj = []
    try:
        data = client.get_ordered(url="orders").json()
        sorted_by_date = sorted(data, key=lambda x: x["date"], reverse=True)
        paginator = Paginator(sorted_by_date, 32)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        logging.warning(e)
    return render(request, "ordered.html", {"data": page_obj})


@login_required
def bought(request):
    client = RestClient(user=request.user)
    page_obj = []
    try:
        data = client.get_ordered(url="sales").json()
        sorted_by_date = sorted(data, key=lambda x: x["date"], reverse=True)
        paginator = Paginator(sorted_by_date, 32)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        logging.warning(e)
    return render(request, "ordered.html", {"data": page_obj})


@login_required
def api(request):
    form = ApiForm(request.POST or None)
    if form.is_valid():
        form.instance.user = request.user
        form.save()
    return render(request, "api.html", {"form": form})
