filtering_lambdas = {
    "all": {
        "func": lambda x: True,
        "desc": "Отобразить все",
    },
    "sales": {
        "func": lambda product: product.sales > 0,
        "desc": "Были продажи за 14 дней",
    },
}

filtering_lambdas_marketplace = filtering_lambdas | {
    "orders": {
        "func": lambda product: product.orders > 0,
        "desc": "Еще не собраны",
    },
}

filtering_lambdas_warehouse = filtering_lambdas | {
    "orders": {
        "func": lambda product: product.orders > 0,
        "desc": "Заказы за 14 дней",
    },
}


def filter_products(products: list, filter_by, lambdas):
    if filter_by not in lambdas:
        return products
    return list(filter(lambdas[filter_by]["func"], products))


def filter_marketplace_products(products, filter_by):
    return filter_products(products, filter_by, filtering_lambdas_marketplace)


def filter_warehouse_products(products, filter_by):
    return filter_products(products, filter_by, filtering_lambdas_warehouse)
