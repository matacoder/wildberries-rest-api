from django.http import HttpResponse
from loguru import logger

from wb.models import ApiKey, Product, Size

from wb.services.redis import redis_cache_decorator
from wb.services.rest_client.jwt_client import JWTApiClient


def get_marketplace_objects(token):
    """Proper way to deal with products."""
    logger.info("Getting marketplace as objects")

    tokens = ApiKey.objects.get(api=token)
    jwt_token = tokens.new_api
    # x64_token = tokens.api

    if not jwt_token:
        return HttpResponse("Нужно указать API-ключ!")

    new_client = JWTApiClient(jwt_token)

    raw_stock = new_client.get_stock()
    stock_products = dict()
    for item in raw_stock:
        # Get or create new product:
        product = stock_products.get(item["nmId"], None)
        if product is None:
            product = Product(
                nm_id=item["nmId"],
                supplier_article=item["article"],
            )
            stock_products[product.nm_id] = product

        # Update product
        # product.price = int(item["Price"] * ((100 - item["Discount"]) / 100))
        # product.full_price = int(item["Price"])
        # product.discount = item["Discount"]
        # product.in_way_to_client = item.get("inWayToClient", 0)
        # product.in_way_from_client = item.get("inWayFromClient", 0)
        product.barcode = item.get("barcode", 0)
        product.name = item.get("name", 0)

        # product.days_on_site = item.get("daysOnSite", 0)

        # Get or create new size
        size = item.get("size", 0)
        product.sizes[size] = product.sizes.get(
            size, Size(tech_size=size)  # Create generic size
        )

        # Update size values
        product.sizes[size].quantity_full = item.get("stock", 0)

    return stock_products


def update_prices(token, stock_products):
    tokens = ApiKey.objects.get(api=token)
    new_token = tokens.new_api
    if not new_token:
        return HttpResponse("Нужно указать API-ключ!")

    new_client = JWTApiClient(new_token)

    prices = new_client.get_prices()

    for price in prices:
        product = stock_products.get(price["nmId"])

        if product:
            product.price = int(price["price"] * ((100 - price["discount"]) / 100))
            product.full_price = int(price["price"])
            product.discount = price["discount"]
    return stock_products


@redis_cache_decorator(minutes=1)
def update_marketplace_prices(token, stock_products):
    """We use proxy function to cache results."""
    return update_prices(token, stock_products)


@redis_cache_decorator(minutes=1)
def update_warehouse_prices(token, stock_products):
    return update_prices(token, stock_products)


def update_marketplace_sales(token, stock_products):
    pass