import json
import logging

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import render

from wb.forms import ApiForm
from wb.services import (
    get_bought_products,
    get_bought_sum,
    get_ordered_products,
    get_ordered_sum,
    get_stock_products,
    get_weekly_payment,
)


def index(request):
    return render(request, "index.html", {})


@login_required
def stock(request):
    data = get_stock_products(user=request.user)
    in_stock = filter(lambda x: x["quantity"] > 0, data)
    sorted_in_stock = sorted(in_stock, key=lambda x: x["quantity"], reverse=True)
    paginator = Paginator(sorted_in_stock, 32)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    data = get_info_widget(request.user)
    data["data"] = page_obj
    return render(
        request,
        "stock.html",
        data,
    )


def get_info_widget(user):
    return {
        "payment": get_weekly_payment(user=user),
        "ordered": get_ordered_sum(user=user),
        "bought": get_bought_sum(user=user),
    }


@login_required
def ordered(request):
    return render_page(get_ordered_products, request)


def render_page(function, request):
    data = function(user=request.user)
    sorted_by_date = sorted(data, key=lambda x: x["date"], reverse=True)
    paginator = Paginator(sorted_by_date, 32)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    data = get_info_widget(request.user)
    data["data"] = page_obj

    return render(
        request,
        "ordered.html",
        data,
    )


@login_required
def bought(request):
    return render_page(get_bought_products, request)


@login_required
def api(request):
    form = ApiForm(request.POST or None)
    if form.is_valid():
        form.instance.user = request.user
        form.save()
    return render(request, "api.html", {"form": form})


@login_required
def weekly_orders_summary(request):
    data = get_ordered_products(user=request.user, week=False, flag=0, days=14)
    combined = dict()
    # logging.warning(data)
    stock = get_stock_as_dict(request)
    for item in data:
        wb_id = item["nmId"]
        sku = item["supplierArticle"]
        size = item["techSize"]
        qty = item["quantity"]
        if wb_id not in combined:
            combined[wb_id] = {
                "sizes": {size: qty},
                "total": qty,
                "sku": sku,
                "stock": stock.get(wb_id, None),
            }
        else:
            editing = combined[wb_id]  # this is pointer to object in memory
            editing["sizes"][size] = editing["sizes"].get(size, 0) + qty
            editing["total"] += qty
    # logging.warning(combined)
    unsorted_data = tuple(combined.items())
    sorted_data = sorted(unsorted_data, key=lambda x: x[1]["total"], reverse=True)
    paginator = Paginator(sorted_data, 32)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    data = get_info_widget(request.user)
    data["data"] = page_obj

    return render(
        request,
        "summary.html",
        data,
    )


def get_stock_as_dict(request):
    data = get_stock_products(user=request.user)
    stock_as_dict = dict()
    for x in data:
        key = x["nmId"]
        stock_as_dict[key] = stock_as_dict.get(key, 0) + x["quantity"]

    return stock_as_dict


@login_required
def add_to_cart(request):
    cart = json.loads(request.session.get("json_cart", '{}'))
    wb_id = request.GET.get("wb_id")
    qty = request.GET.get("qty")
    cart[wb_id] = cart.get(wb_id, 0) + int(qty)
    request.session["json_cart"] = json.dumps(cart)
    return HttpResponse(len(cart))
