import concurrent.futures
import datetime
import json
import logging
import pickle
from multiprocessing.pool import ThreadPool
from rest_framework.decorators import api_view

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from loguru import logger
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from _settings.settings import redis_client
from wb.forms import ApiForm
from wb.models import ApiKey
from wb.services.filtering import (
    filter_marketplace_products,
    filter_warehouse_products,
    filtering_lambdas_marketplace,
    filtering_lambdas_warehouse,
)
from wb.services.json_encoder import ObjectDict
from wb.services.marketplace import (
    get_marketplace_objects,
    update_marketplace_prices,
    update_marketplace_sales,
    update_warehouse_prices,
)
from wb.services.rest_client.standard_client import StandardApiClient
from wb.services.search import search_warehouse_products
from wb.services.sorting import (
    get_marketplaces_sorting,
    sort_marketplace_products,
    sort_products,
    sorting_lambdas,
)
from wb.services.statistics import get_sales_statistics, get_stock_statistics
from wb.services.tools import api_key_required
from wb.services.warehouse import (
    add_weekly_orders,
    add_weekly_sales,
    get_bought_products,
    get_ordered_products,
    get_stock_objects,
    get_stock_products, attach_images,
)


def index(request):
    # https://images.wbstatic.net/portal/education/Kak_rabotat'_s_servisom_statistiki.pdf
    # https://suppliers-api.wildberries.ru/swagger/index.html
    # https://openapi.wb.ru/
    return render(request, "index.html", {})


@login_required
@api_key_required
def update_discount(request):
    tokens = ApiKey.objects.get(user=request.user)
    jwt_token = tokens.new_api
    x64_token = tokens.api
    timezone = 3  # Moscow time

    if not jwt_token:
        return HttpResponse("Нужно указать API-ключ!")

    new_client = StandardApiClient(jwt_token)
    wb_id = request.GET.get("wb_id")

    new_price = int(request.GET.get("new_price"))
    if new_price:
        full_price = int(request.GET.get("full_price"))
        new_discount = int(100 - new_price * 100 / full_price)
        logger.info(f"Посчитана скидка в {new_discount}%")
    else:
        new_discount = int(request.GET.get("new_discount"))
    if new_discount is not None:
        success, message = new_client.update_discount(wb_id, new_discount)
        if success:
            redis_key = f"{x64_token}:update_discount:{wb_id}"
            now = datetime.datetime.now(
                datetime.timezone(datetime.timedelta(hours=timezone))
            )
            logger.info(f"{now}, {datetime.datetime.now()}")
            redis_value = pickle.dumps(
                {
                    "new_price": new_price,
                    "new_discount": new_discount,
                    # A bit creepy way to introduce timezone +3 MSK
                    "modified_at": datetime.datetime.now(
                        datetime.timezone(datetime.timedelta(hours=timezone))
                    ),
                }
            )
            redis_client.set(
                redis_key, redis_value, ex=60 * 60 * 24 * 14
            )  # Keep info about price change for 14 days
            return HttpResponse(f"Установлена {new_discount}% скидка")
        return HttpResponse(message)


@login_required
@api_key_required
def stock(request):
    """Display products in stock."""
    logger.info("View: requested stock")
    statistics_token = ApiKey.objects.get(user=request.user.id).api
    standard_token = ApiKey.objects.get(user=request.user.id).new_api

    # Statistics have 3 requests that take 30+ seconds, so we start another thread pool here
    # Tread doesn't support return value!
    pool = ThreadPool(processes=1)
    async_result = pool.apply_async(get_sales_statistics, (statistics_token,))
    # and actually 3 more threads inside. Magic!

    # So here actually we have 4 concurrent requests
    products = get_stock_objects(statistics_token)
    products = add_weekly_sales(statistics_token, products)
    products = add_weekly_orders(statistics_token, products)
    products = update_warehouse_prices(statistics_token, products)
    products = attach_images(standard_token, products)
    products = list(products.values())

    sort_by = request.GET.get("sort_by")

    products = sort_products(products, sort_by)

    filter_by = request.GET.get("filter_by")
    if filter_by:
        products = filter_warehouse_products(products, filter_by)

    search_keyword = request.GET.get("search")
    if search_keyword:
        products = search_warehouse_products(products, search_keyword)

    # Ready to paginate
    paginator = Paginator(products, 32)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Get our statistics
    data = async_result.get()

    data["data"] = page_obj
    data = data | get_stock_statistics(products)
    data["sorting_lambdas"] = sorting_lambdas
    data["filtering_lambdas"] = filtering_lambdas_warehouse

    return render(
        request,
        "stock.html",
        data,
    )


x64_token = openapi.Parameter(
    "x64_token",
    openapi.IN_QUERY,
    description="x64_token https://seller.wb.ru/supplier-settings/access-to-api",
    type=openapi.TYPE_STRING,
)
jwt_token = openapi.Parameter(
    "jwt_token",
    openapi.IN_QUERY,
    description="jwt_token https://seller.wb.ru/supplier-settings/access-to-new-api",
    type=openapi.TYPE_STRING,
)


@swagger_auto_schema(method="get", manual_parameters=[x64_token])
@api_view(http_method_names=["GET"])
def api_stock(request):
    if "x64_token" not in request.GET:
        return JsonResponse({"error": "x64_token is not provided"})
    token = request.GET["x64_token"]
    products = get_stock_objects(token)
    products = add_weekly_sales(token, products)
    products = add_weekly_orders(token, products)
    products = update_warehouse_prices(token, products)
    return JsonResponse(products, encoder=ObjectDict, json_dumps_params={"indent": 4})


@login_required
@api_key_required
def marketplace(request):
    """Display products in marketplace."""
    logger.info("View: requested marketplace")
    tokens = ApiKey.objects.get(user=request.user)
    jwt_token = tokens.new_api
    x64_token = tokens.api

    # Statistics have 3 requests that take 30+ seconds, so we start another thread pool here
    # Tread doesn't support return value!
    pool = ThreadPool(processes=1)
    async_result = pool.apply_async(get_sales_statistics, (x64_token,))
    # and actually 3 more threads inside. Magic!

    # So here actually we have 4 concurrent requests
    products, barcode_hashmap = get_marketplace_objects(x64_token)
    products = update_marketplace_prices(x64_token, products)
    products = update_marketplace_sales(jwt_token, products, barcode_hashmap)
    products = attach_images(jwt_token, products)

    products = list(products.values())
    sort_by = request.GET.get("sort_by")
    products = sort_marketplace_products(products, sort_by)

    filter_by = request.GET.get("filter_by")
    if filter_by:
        products = filter_marketplace_products(products, filter_by)

    search_keyword = request.GET.get("search")
    if search_keyword:
        products = search_warehouse_products(products, search_keyword)
    # Ready to paginate
    paginator = Paginator(products, 32)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Get our weekly revenue and sales/orders
    data = async_result.get()

    data["data"] = page_obj

    data = data | get_stock_statistics(products)
    data["sorting_lambdas"] = get_marketplaces_sorting()
    data["filtering_lambdas"] = filtering_lambdas_marketplace

    data["marketplace"] = True

    return render(
        request,
        "stock.html",
        data,
    )


@swagger_auto_schema(method="get", manual_parameters=[x64_token, jwt_token])
@api_view(http_method_names=["GET"])
def api_marketplace(request):
    if "x64_token" not in request.GET or "jwt_token" not in request.GET:
        return JsonResponse({"error": "x64_token or jwt_token are not provided"})
    x64_token = request.GET["x64_token"]
    jwt_token = request.GET["jwt_token"]
    products, barcode_hashmap = get_marketplace_objects(x64_token)
    products = update_marketplace_prices(x64_token, products)
    products = update_marketplace_sales(jwt_token, products, barcode_hashmap)

    return JsonResponse(products, encoder=ObjectDict, json_dumps_params={"indent": 4})


@login_required
@api_key_required
def ordered(request):
    return render_page(get_ordered_products, request)


def render_page(function, request):
    # Statistics have 3 requests that take 30+ seconds, so we start another thread pool here
    # Tread doesn't support return value!
    token = ApiKey.objects.get(user=request.user.id).api
    pool = ThreadPool(processes=1)
    async_result = pool.apply_async(get_sales_statistics, (token,))
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

    if ApiKey.objects.filter(user=request.user.id).exists():
        api = ApiKey.objects.get(user=request.user.id)
    else:
        api = None
    form = ApiForm(request.POST or None, instance=api)
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
    async_result = pool.apply_async(get_sales_statistics, (token,))
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
        qty = item.get("quantity", 0)
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

        data["in"] = data.get("in", 0) + item.get("inWayToClient",0)
        data["out"] = data.get("out", 0) + item.get("inWayFromClient",0)
        data["stock"] = data.get("stock", 0) + item.get("quantityFull",0)

        sizes = data.get("sizes", dict())
        size = item.get("techSize", 0)
        sizes[size] = sizes.get(size, 0) + item.get("quantityFull",0)

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
