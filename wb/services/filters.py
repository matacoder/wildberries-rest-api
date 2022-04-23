from wb.models import Product

sorting_lambdas = {
    "qty": {
        "func": lambda product: product.stock,
        "desc": "Остатки"
    },
    "sales": {
        "func": lambda product: product.sales,
        "desc": "Продажи"
    },
    "order_now": {
        "func": lambda product: product.sales / product.stock if product.stock > 0 else product.sales / 0.9,
        "desc": "Пора заказывать"
    }
}


def sort_products(products: list[Product], filter_by: str = "qty") -> list[Product]:
    if filter_by not in sorting_lambdas:
        filter_by = "qty"

    return sorted(products, key=sorting_lambdas[filter_by]["func"], reverse=True)
