from typing import List

from wb.models import Product


def search_warehouse_products(products: List[Product], keyword):
    found = []
    keyword = str(keyword).lower()
    for product in products:
        if (
            keyword in str(product.name).lower()
            or keyword in str(product.supplier_article).lower()
            or keyword in str(product.nm_id).lower()
        ):
            found.append(product)
    return found
