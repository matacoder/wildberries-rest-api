from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class ApiKey(models.Model):
    api = models.CharField(max_length=200)
    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True)

    def __str__(self):
        return self.api


class ProductCard(models.Model):
    wb_id = models.CharField(max_length=200)
    supplier_sku = models.CharField(max_length=200)
    price = models.IntegerField()
    discount = models.IntegerField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, unique=True)


class ProductSize(models.Model):
    product_card = models.ForeignKey(ProductCard, on_delete=models.CASCADE, unique=True)
    size = models.CharField(max_length=200)
    to_customer = models.IntegerField()
    from_customer = models.IntegerField()
    barcode = models.CharField(max_length=200)
    quantity = models.IntegerField()
    in_way_to_client = models.IntegerField()
    in_way_from_client = models.IntegerField()
    subject = models.CharField(max_length=200)
    category = models.CharField(max_length=200)
    days_on_site = models.IntegerField()
    brand = models.CharField(max_length=200)


class Sale(models.Model):
    order_id = models.CharField(max_length=200)
    document = models.CharField(max_length=200)
    sale_date = models.CharField(max_length=200)
    last_modified = models.CharField(max_length=200)
    product_size = models.ForeignKey(ProductSize, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    discount = models.IntegerField()
    promo_code = models.IntegerField()
    warehouse = models.CharField(max_length=200)
    country = models.CharField(max_length=200)
    oblast = models.CharField(max_length=200)
    region = models.CharField(max_length=200)
    supply_id = models.IntegerField()
    sale_id = models.IntegerField()
    spp = models.IntegerField()
    forpay = models.IntegerField()
    finished_price = models.IntegerField()
    price_with_discount = models.IntegerField()
    subject = models.CharField(max_length=200)
    category = models.CharField(max_length=200)
    brand = models.CharField(max_length=200)
