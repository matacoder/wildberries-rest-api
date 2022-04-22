import pickle
import time

from loguru import logger

from _settings.settings import redis_client
from wb.models import Product, Sale, Size
from wb.services.redis import redis_cache_decorator
from wb.services.rest_client.x64_client import RETRY_DELAY, X64ApiClient


def get_stock_objects(x64_token):
    """Proper way to deal with products."""
    logger.info("Getting stock as objects")
    raw_stock = get_stock_products(x64_token)
    stock_products = dict()

    for item in raw_stock:
        # Get or create new product:
        product = stock_products.get(item["nmId"], None)
        if product is None:
            product = Product(
                nm_id=item["nmId"],
                supplier_article=item["supplierArticle"],
            )
            stock_products[product.nm_id] = product

        # Update product
        product.price = int(item["Price"] * ((100 - item["Discount"]) / 100))
        product.full_price = int(item["Price"])
        product.discount = item["Discount"]
        product.in_way_to_client = item.get("inWayToClient", 0)
        product.in_way_from_client = item.get("inWayFromClient", 0)
        product.barcode = item.get("barcode", 0)
        product.days_on_site = item.get("daysOnSite", 0)

        redis_key = f"{x64_token}:update_discount:{product.nm_id}"
        has_been_updated = redis_client.get(redis_key)
        if has_been_updated is not None:
            logger.info(f"Found update info for {product.nm_id}")
            product.has_been_updated = pickle.loads(has_been_updated)

        # Get or create new size
        size = item.get("techSize", 0)
        product.sizes[size] = product.sizes.get(
            size, Size(tech_size=size)  # Create generic size
        )

        # Update size values
        product.sizes[size].quantity_full = item.get("quantityFull", 0)

    return stock_products


def add_weekly_sales(token, stock_products: dict):
    """Add sales to stock products."""
    logger.info("Applying 14 days sales to stock...")
    # Get sales endpoint
    raw_sales = get_ordered_products(token=token, week=False, flag=0, days=14)

    for raw_sale in raw_sales:
        product: Product = stock_products.get(raw_sale["nmId"])
        if product is None:
            # Not sure why stock is not displaying all products
            product = Product(
                nm_id=raw_sale.get("nmId"),
                supplier_article=raw_sale.get("supplierArticle"),
            )
            stock_products[product.nm_id] = product
        size = raw_sale["techSize"]
        product.size = product.sizes.get(
            size,
            Size(tech_size=raw_sale.get("techSize", 0)),  # Create generic size
        )

        sale = Sale(
            quantity=raw_sale["quantity"],
        )

        sale.date = raw_sale.get("date")
        sale.price_with_disc = float(raw_sale.get("priceWithDisc", 0))
        sale.finished_price = float(raw_sale.get("finishedPrice", 0))
        sale.for_pay = float(raw_sale.get("forPay", 0))

        product.size.sales.append(sale)

    return stock_products


@redis_cache_decorator()
def get_weekly_payment(token):
    logger.info("Getting weekly payment...")
    data = get_bought_products(token, week=True, flag=0)
    if data:
        payment = sum((x["forPay"]) for x in data)
        return int(payment)
    return 0


@redis_cache_decorator()
def get_ordered_sum(token):
    logger.info("Getting ordered payment...")
    data = get_ordered_products(token)
    if data:
        return int(
            sum((x["totalPrice"] * (1 - x["discountPercent"] / 100)) for x in data)
        )
    return 0


@redis_cache_decorator()
def get_bought_sum(token):
    logger.info("Getting bought payment...")
    data = get_bought_products(token)
    if data:
        return int(sum((x["forPay"]) for x in data))
    return 0


@redis_cache_decorator()
def get_ordered_products(token, week=False, flag=1, days=None):
    client = X64ApiClient(token)
    data = client.get_ordered(url="orders", week=week, flag=flag, days=days)
    attempt = 0
    while data.status_code != 200:
        attempt += 1
        if attempt > 10:
            return {}
        logger.info("WB endpoint is faulty. Retrying...")
        time.sleep(RETRY_DELAY)
        data = client.get_ordered(url="orders", week=week, flag=flag, days=days)
    return data.json()


@redis_cache_decorator()
def get_bought_products(token, week=False, flag=1):
    client = X64ApiClient(token)
    data = client.get_ordered(url="sales", week=week, flag=flag)
    attempt = 0
    while data.status_code != 200:
        attempt += 1
        if attempt > 10:
            return {}
        logger.info("WB endpoint is faulty. Retrying...")
        time.sleep(RETRY_DELAY)
        data = client.get_ordered(url="sales", week=week, flag=flag)
    return data.json()


@redis_cache_decorator()
def get_stock_products(token):
    """Getting products in stock."""
    logger.info("Getting products in stock.")
    client = X64ApiClient(token)
    data = client.get_stock()
    logger.info(data)
    attempt = 0
    while data.status_code != 200:
        attempt += 1
        if attempt > 10:
            return {}
        logger.info("WB endpoint is faulty. Retrying...")
        time.sleep(RETRY_DELAY)
        data = client.get_stock()
    logger.info(data.text[:100])
    return data.json()
