import concurrent.futures

from loguru import logger

from wb.models import Product
from wb.services.warehouse import get_weekly_payment, get_ordered_sum, get_bought_sum


def get_stock_statistics(products: list[Product]) -> dict:
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

    return {
        "total_sku": total_sku,
        "total": total_qty,
        "can_be_ordered_qty": can_be_ordered_qty,
        "total_value": total_value,
    }


def get_sales_statistics(token):
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

    return result
