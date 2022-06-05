from django.http import HttpResponse
from loguru import logger

from wb.models import ApiKey, Product, Sale, Size
from wb.services.redis import get_price_change_from_redis, redis_cache_decorator
from wb.services.rest_client.jwt_client import JWTApiClient


def get_marketplace_objects(token):
    """Proper way to deal with products."""
    logger.info("Getting marketplace as objects")

    # Okay, for people with several accounts we must get latest
    tokens = ApiKey.objects.filter(api=token)
    tokens = tokens.last()
    jwt_token = tokens.new_api
    x64_token = tokens.api

    if not jwt_token:
        return HttpResponse("Нужно указать API-ключ!")

    new_client = JWTApiClient(jwt_token)

    raw_stock = new_client.get_stock()
    stock_products = dict()

    # For some reason WB don't use wb_id in marketplace sales
    # So to increase speed pf access we create barcode -> wb_id hash
    barcode_hashmap = dict()

    for item in raw_stock:
        # Get or create new product:
        product = stock_products.get(item["nmId"], None)
        if product is None:
            product = Product(
                nm_id=item["nmId"],
                supplier_article=item["article"],
            )
            stock_products[product.nm_id] = product

        product.name = item.get("name", 0)

        product = get_price_change_from_redis(product, x64_token)

        # Get or create new size
        size = item.get("size", 0)
        product.sizes[size] = product.sizes.get(
            size, Size(tech_size=size)  # Create generic size
        )

        # Update size values
        product.sizes[size].quantity_full = item.get("stock", 0)
        product.sizes[size].barcode = item.get("barcode", 0)
        barcode_hashmap[item.get("barcode", 0)] = (
            product.nm_id,
            item.get("size", 0),
        )

    return stock_products, barcode_hashmap


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


@redis_cache_decorator(minutes=1)
def update_marketplace_sales(token, stock_products, barcode_hashmap):
    jwt_client = JWTApiClient(token)
    orders = jwt_client.get_orders(days=14)

    for order in orders:
        wm_id, size_id = barcode_hashmap.get(order["barcode"], (None, None, ))
        if not wm_id:
            logger.info(f"{order['barcode']} is not found in products")
            continue
        product = stock_products.get(wm_id)
        if not product:
            continue
        size: Size = product.sizes.get(size_id, Size(size_id))
        status = int(order.get("status"))
        sale = Sale(
            date=order.get("dateCreated"),
            quantity=1,
            finished_price=float(order.get("totalPrice") / 100),
        )
        if status == 0:
            # Fresh new orders, must be processed immediately!
            size.orders.append(sale)
        else:
            size.sales.append(sale)

    return stock_products
