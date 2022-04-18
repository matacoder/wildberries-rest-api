import concurrent.futures
import json
import logging
from multiprocessing.pool import ThreadPool

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import render
from loguru import logger

from _settings.settings import redis_client
from wb.forms import ApiForm
from wb.models import ApiKey
from wb.services.services import (
    api_key_required,
    get_bought_products,
    get_bought_sum,
    get_ordered_products,
    get_ordered_sum,
    get_stock_products,
    get_weekly_payment,
)
from wb.services.warehouse import get_stock_objects, add_weekly_sales


def index(request):
    big_data = {"key": "value"}
    redis_client.set("foo", json.dumps(big_data))
    logger.info(redis_client.get("foo"))
    return render(request, "index.html", {})


# https://images.wbstatic.net/portal/education/Kak_rabotat'_s_servisom_statistiki.pdf


@login_required
@api_key_required
def stock(request):
    """Display products in stock."""
    logger.info("View: requested stock")
    token = ApiKey.objects.get(user=request.user.id).api

    # Statistics have 3 requests that take 30+ seconds, so we start another thread pool here
    # Tread doesn't support return value!
    pool = ThreadPool(processes=1)
    async_result = pool.apply_async(get_info_widget, (token,))
    # and actually 3 more threads inside. Magic!

    # So here actually we have 4 concurrent requests
    products = get_stock_objects(token)
    products = add_weekly_sales(token, products)
    products = list(products.values())
    products = sorted(products, key=lambda product: product.stock, reverse=True)

    # Ready to paginate
    paginator = Paginator(products, 32)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Get our statistics
    data = async_result.get()
    logger.info(f"{data=}")

    # General statistics
    total_sku = 0
    total_qty = 0
    total_value = 0
    can_be_ordered_qty = 0
    for product in products:
        total_sku += 1
        total_qty += product.stock
        if (product.stock - product.in_way_to_client - product.in_way_from_client) > 0:
            can_be_ordered_qty += 1
        total_value += product.stock * product.price

    data["data"] = page_obj
    data["total_sku"] = total_sku
    data["total"] = total_qty
    data["can_be_ordered_qty"] = can_be_ordered_qty
    data["total_value"] = total_value

    return render(
        request,
        "stock.html",
        data,
    )


def get_info_widget(token):
    """Concurrent request for common data."""
    logger.info("Concurrent request for statistics...")
    target_functions = [
        get_weekly_payment,
        get_ordered_sum,
        get_bought_sum,
    ]
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for target_function in target_functions:
            futures.append(executor.submit(target_function, token))
        result = {
            "payment": futures[0].result(),
            "ordered": futures[1].result(),
            "bought": futures[2].result(),
        }
        logger.info(f"{result=}")

    return result


@login_required
@api_key_required
def ordered(request):
    return render_page(get_ordered_products, request)


def render_page(function, request):
    # Statistics have 3 requests that take 30+ seconds, so we start another thread pool here
    # Tread doesn't support return value!
    token = ApiKey.objects.get(user=request.user.id).api
    pool = ThreadPool(processes=1)
    async_result = pool.apply_async(get_info_widget, (token,))
    # and actually 3 more threads inside. Magic!

    data = function(token)
    sorted_by_date = sorted(data, key=lambda x: x["date"], reverse=True)
    paginator = Paginator(sorted_by_date, 32)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Get our statistics
    data = async_result.get()

    data["data"] = page_obj

    return render(
        request,
        "ordered.html",
        data,
    )


@login_required
@api_key_required
def bought(request):
    return render_page(get_bought_products, request)


@login_required
def api(request):
    logger.info("Api page requested...")
    form = ApiForm(request.POST or None)
    if ApiKey.objects.filter(user=request.user.id).exists():
        api = ApiKey.objects.get(user=request.user.id)
    else:
        api = False
    if form.is_valid():
        form.instance.user = request.user
        form.save()
    return render(request, "api.html", {"form": form, "api": api})


@login_required
@api_key_required
def weekly_orders_summary(request):
    # Statistics have 3 requests that take 30+ seconds, so we start another thread pool here
    # Tread doesn't support return value!
    token = ApiKey.objects.get(user=request.user.id).api
    pool = ThreadPool(processes=1)
    async_result = pool.apply_async(get_info_widget, (token,))
    # and actually 3 more threads inside. Magic!

    with concurrent.futures.ThreadPoolExecutor() as executor:
        logger.info("Concurrent analytics dicts")
        future1 = executor.submit(
            get_ordered_products, token=token, week=False, flag=0, days=14
        )
        future2 = executor.submit(get_stock_as_dict, request)
        data = future1.result()
        stock = future2.result()
    logger.info("We've got STOCK and DATA")

    combined = dict()
    to_order = request.GET.get("to_order", False)

    for item in data:

        wb_id = item["nmId"]
        sku = item["supplierArticle"]
        size = item["techSize"]
        qty = item["quantity"]
        stock_data = stock.get(wb_id, {"stock": 0})

        if wb_id not in combined:
            combined[wb_id] = {
                "sizes": {size: qty},
                "total": qty,
                "sku": sku,
                "stock": stock_data.get("stock", 0),
                "stock_sizes": stock_data.get("sizes", dict()),
            }
        else:
            editing = combined[wb_id]  # this is pointer to object in memory
            editing["sizes"][size] = editing["sizes"].get(size, 0) + qty
            editing["total"] += qty
            editing["stock_sizes"] = (stock_data.get("sizes", dict()),)

    unsorted_data = tuple(combined.items())
    sorted_data = sorted(unsorted_data, key=lambda x: x[1]["total"], reverse=True)
    if to_order:
        sorted_data = tuple(
            filter(lambda x: x[1]["total"] > x[1]["stock"], sorted_data)
        )
    paginator = Paginator(sorted_data, 32)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Get our statistics
    data = async_result.get()
    data["data"] = page_obj

    return render(
        request,
        "summary.html",
        data,
    )


def get_stock_as_dict(request):
    """Must be rewritten with saving to DB"""
    logger.info("Getting stock as dict")
    token = ApiKey.objects.get(user=request.user.id).api
    stock = get_stock_products(token)
    stock_as_dict = dict()
    for item in stock:
        key = item["nmId"]  # wb_id
        price = int(item["Price"] * ((100 - item["Discount"]) / 100))
        data = {
            "wb_id": item["nmId"],
            "sku": item["supplierArticle"],
            "price": price,
        }
        data = stock_as_dict.get(key, data)

        data["in"] = data.get("in", 0) + item["inWayToClient"]
        data["out"] = data.get("out", 0) + item["inWayFromClient"]
        data["stock"] = data.get("stock", 0) + item["quantityFull"]

        sizes = data.get("sizes", dict())
        size = item.get("techSize", 0)
        sizes[size] = sizes.get(size, 0) + item["quantityFull"]

        data["sizes"] = sizes
        stock_as_dict[key] = data

    logging.warning(stock_as_dict.get(11034009, None))

    return stock_as_dict


@login_required
@api_key_required
def add_to_cart(request):
    cart = json.loads(request.session.get("json_cart2", "{}"))

    wb_id = request.GET.get("wb_id")
    qty = request.GET.get("qty")
    sku = request.GET.get("sku")
    size = request.GET.get("size")
    update = request.GET.get("update", False)
    logging.warning(sku)

    item = cart.get(wb_id, dict())
    item["sku"] = sku
    sizes = item.get("sizes", dict())
    if update:
        sizes[size] = int(qty)
    else:
        sizes[size] = sizes.get(size, 0) + int(qty)
    if sizes[size] == 0:
        sizes.pop(size, None)
    if not sizes:
        cart.pop(wb_id, None)
    else:
        item["sizes"] = sizes
        cart[wb_id] = item

    request.session["json_cart2"] = json.dumps(cart)
    return HttpResponse(len(cart))


@login_required
@api_key_required
def cart(request):
    cart = json.loads(request.session.get("json_cart2", "{}"))
    logging.warning(cart)
    cart = tuple(cart.items())
    logging.warning(cart)
    paginator = Paginator(cart, 32)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    data = dict()
    data["data"] = page_obj

    return render(
        request,
        "cart.html",
        data,
    )
