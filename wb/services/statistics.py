import concurrent.futures

from loguru import logger

from wb.models import Product
from wb.services.warehouse import (get_bought_sum, get_ordered_sum,
                                   get_weekly_payment)


def get_stock_statistics(products: list[Product]) -> dict:
    stat = {}
    for product in products:
        stat["total_sku"] = stat.get("total_sku", 0) + 1
        stat["total"] = stat.get("total", 0) + product.stock
        stat["total_in_stock"] = (
            stat.get("total_in_stock", 0)
            + product.stock
            - product.in_way_to_client
            - product.in_way_from_client
        )
        stat["in_the_way"] = (
            stat.get("in_the_way", 0)
            + product.in_way_to_client
            + product.in_way_from_client
        )
        stat["total_value"] = stat.get("total_value", 0) + product.stock * product.price

        if (product.stock - product.in_way_to_client - product.in_way_from_client) > 0:
            stat["can_be_ordered_qty"] = stat.get("can_be_ordered_qty", 0) + 1
        else:
            stat["sku_on_the_way"] = stat.get("sku_on_the_way", 0) + 1

    return stat


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
