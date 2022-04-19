from dataclasses import dataclass, field

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class ApiKey(models.Model):
    api = models.CharField(max_length=200, verbose_name="Ключ API (x64)")
    new_api = models.CharField(max_length=400, default="", verbose_name="Ключ нового API (JWT)")
    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True)

    def __str__(self):
        return self.api


@dataclass
class Product:
    """WB product."""
    nm_id: int  # nmId (Wildberries sku number)
    supplier_article: str = ""
    full_price: int = 0  # Price without discount
    price: float = 0  # Price
    discount: float = 0  # Discount
    sizes: dict = field(default_factory=dict)
    in_way_to_client: int = 0  # inWayToClient
    in_way_from_client: int = 0  # inWayFromClient
    barcode: str = ""
    days_on_site: str = ""

    @property
    def stock(self):
        return sum(size.quantity_full for size in self.sizes.values())


@dataclass
class Size:
    """WB size."""
    tech_size: str = 0  # techSize
    quantity_full: int = 0  # quantityFull
    sales: list = field(default_factory=list)
    orders: list = field(default_factory=list)

    @property
    def total_sales(self):
        return len(self.sales)


@dataclass
class Sale:
    """WB sale."""
    date: str = ""
    quantity: int = 0
    price_with_disc: float = 0
    finished_price: float = 0
    for_pay: float = 0


@dataclass
class Order:
    """WB sale with Product attached."""
    quantity: int = 0
    product: Product = None
