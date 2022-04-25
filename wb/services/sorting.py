from copy import deepcopy

from wb.models import Product

sorting_lambdas = {
    "qty": {"func": lambda product: product.stock, "desc": "Остатки"},
    "sales": {"func": lambda product: product.sales, "desc": "Продажи"},
    "orders": {"func": lambda product: product.orders, "desc": "Заказы"},
    "order_now": {
        "func": lambda product: product.orders / product.stock
        if product.stock > 0
        else product.orders / 0.7,
        "desc": "Срочно заказывать",
    },
    "out_of_stock_soon": {
        "func": lambda product: product.orders if product.stock < product.orders else 0,
        "desc": "Скоро закончится",
    },
    "low_sales": {
        "func": lambda product: product.stock / product.orders
        if product.orders > 0
        else product.stock / 0.7,
        "desc": "Плохо продаются",
    },
}


def get_marketplaces_sorting():
    """Orders in marketplace are unprocessed entities, and after processing they disappear.
    So we have to use sales instead in lambdas."""
    marketplace_sorting_lambdas = deepcopy(sorting_lambdas)
    marketplace_sorting_lambdas.pop("orders")
    marketplace_sorting_lambdas["order_now"]["func"] = (
        lambda product: product.sales / product.stock
        if product.stock > 0
        else product.orders / 0.7
    )
    marketplace_sorting_lambdas["out_of_stock_soon"]["func"] = (
        lambda product: product.sales if product.stock < product.sales else 0
    )
    marketplace_sorting_lambdas["low_sales"]["func"] = (
        lambda product: product.stock / product.sales
        if product.sales > 0
        else product.stock / 0.7
    )
    return marketplace_sorting_lambdas


def sort_marketplace_products(
    products: list[Product], filter_by: str = "qty"
) -> list[Product]:
    return sort_products(products, filter_by, get_marketplaces_sorting())


def sort_products(
    products: list[Product], filter_by: str = "qty", lambdas=None
) -> list[Product]:
    if lambdas is None:
        lambdas = sorting_lambdas
    if filter_by not in lambdas:
        filter_by = "low_sales"

    return sorted(products, key=lambdas[filter_by]["func"], reverse=True)
