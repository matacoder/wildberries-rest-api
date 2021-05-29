import logging

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
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
