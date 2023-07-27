import time

from loguru import logger

from wb.models import Product, Sale, Size
from wb.services.redis import get_price_change_from_redis, redis_cache_decorator
from wb.services.rest_client.standard_client import StandardApiClient
from wb.services.rest_client.statistics_client import RETRY_DELAY, StatisticsApiClient


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
        product.subject = item.get('subject', "")
        product.category = item.get('category', "")
        product.brand = item.get('brand', "")

        product.full_price = int(item["Price"])
        product.discount = item["Discount"]
        product.in_way_to_client = item.get("inWayToClient", 0)
        product.in_way_from_client = item.get("inWayFromClient", 0)

        product.days_on_site = item.get("daysOnSite", 0)

        product = get_price_change_from_redis(product, x64_token)

        # Get or create new size
        size = item.get("techSize", 0)
        product.sizes[size] = product.sizes.get(
            size, Size(tech_size=size)  # Create generic size
        )

        # Update size values
        product.sizes[size].quantity_full = item.get("quantityFull", 0)
        product.sizes[size].barcode = item.get("barcode", 0)

    return stock_products


def add_weekly_sales(token, stock_products: dict):
    """Add sales to stock products.
    Actually not sales but orders!"""
    logger.info("Applying 14 days sales to stock...")
    # Get sales endpoint
    raw_sales = get_bought_products(token=token, week=False, flag=0, days=14)

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
        product.sizes[size] = product.sizes.get(
            size,
            Size(tech_size=raw_sale.get("techSize", 0)),  # Create generic size
        )

        sale = Sale(quantity=raw_sale.get("quantity", 0))

        sale.date = raw_sale.get("date")
        sale.price_with_disc = float(raw_sale.get("priceWithDisc", 0))
        sale.finished_price = float(raw_sale.get("finishedPrice", 0))
        sale.for_pay = float(raw_sale.get("forPay", 0))

        product.sizes[size].sales.append(sale)

    return stock_products


def add_weekly_orders(token, stock_products: dict):
    """Weekly orders."""
    logger.info("Applying 14 days orders to stock...")
    raw_orders = get_ordered_products(token=token, week=False, flag=0, days=14)

    for raw_order in raw_orders:
        product: Product = stock_products.get(raw_order["nmId"])
        if product is None:
            # Not sure why stock is not displaying all products
            product = Product(
                nm_id=raw_order.get("nmId"),
                supplier_article=raw_order.get("supplierArticle"),
            )
            stock_products[product.nm_id] = product
        size = raw_order["techSize"]
        product.sizes[size] = product.sizes.get(
            size,
            Size(tech_size=raw_order.get("techSize", 0)),  # Create generic size
        )

        sale = Sale(quantity=raw_order.get("quantity", 0))

        sale.date = raw_order.get("date")
        sale.price_with_disc = float(raw_order.get("priceWithDisc", 0))
        sale.finished_price = float(raw_order.get("finishedPrice", 0))
        sale.for_pay = float(raw_order.get("forPay", 0))

        product.sizes[size].orders.append(sale)
    return stock_products


@redis_cache_decorator()
def get_weekly_payment(token):
    logger.info("Getting weekly payment...")
    data = get_bought_products(token, week=True, flag=0)
    if data:
        payment = sum((x.get("forPay", 0)) for x in data)
        return int(payment)
    return 0


@redis_cache_decorator()
def get_ordered_sum(token):
    logger.info("Getting ordered payment...")
    data = get_ordered_products(token)
    if data:
        return int(
            sum(
                (x.get("totalPrice", 0) * (1 - x.get("discountPercent", 0) / 100))
                for x in data
            )
        )
    return 0


@redis_cache_decorator()
def get_bought_sum(token):
    logger.info("Getting bought payment...")
    data = get_bought_products(token)
    if data:
        return int(sum((x.get("forPay", 0)) for x in data))
    return 0


@redis_cache_decorator()
def get_ordered_products(token, week=False, flag=1, days=None):
    client = StatisticsApiClient(token)
    data = client.get_ordered(url="orders", week=week, flag=flag, days=days)
    attempt = 0
    while data.status_code != 200:
        attempt += 1
        if attempt > 10:
            return {}
        logger.info(f"Orders error {data.status_code}, Message: {data.text}")
        time.sleep(RETRY_DELAY)
        data = client.get_ordered(url="orders", week=week, flag=flag, days=days)
    return data.json()


@redis_cache_decorator()
def get_bought_products(token, week=False, flag=1, days=None):
    client = StatisticsApiClient(token)
    data = client.get_ordered(url="sales", week=week, flag=flag, days=days)
    attempt = 0
    while data.status_code != 200:
        attempt += 1
        if attempt > 10:
            return {}
        logger.info(f"Sales error {data.status_code}, Message: {data.text}")
        time.sleep(RETRY_DELAY)
        data = client.get_ordered(url="sales", week=week, flag=flag, days=days)
    return data.json()


@redis_cache_decorator()
def get_stock_products(token):
    """Getting products in stock."""
    logger.info("Getting products in stock.")
    client = StatisticsApiClient(token)
    data = client.get_stock()
    logger.info(data)
    attempt = 0
    while data.status_code != 200:
        attempt += 1
        if attempt > 10:
            return {}
        logger.info(f"Stock error {data.status_code}, Message: {data.text}")
        time.sleep(RETRY_DELAY)
        data = client.get_stock()
    logger.info(data.text[:100])
    return data.json()


@redis_cache_decorator(60)
def attach_images(standard_token, products: dict):
    logger.info("Attaching images...")
    client = StandardApiClient(standard_token)
    images = client.get_content()
    for wb_id, product in products.items():
        if wb_id in images:
            product.image = images[wb_id]["image"]
            product.object = images[wb_id]["object"]
    return products
