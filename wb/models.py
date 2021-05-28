from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class ApiKey(models.Model):
    api = models.CharField(max_length=100)
    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True)

    def __str__(self):
        return self.api


# class OrderedItem(models.Model):
#     number
#     date
#     lastChangeDate
#     supplierArticle
#     techSize
#     barcode
#     quantity
#     totalPrice
#     discountPercent
#     isSupply
#     isRealization
#     orderId
#     promoCodeDiscount
#     warehouseName
#     countryName
#     oblastOkrugName
#     regionName
#     incomeID
#     saleID
#     odid
#     subject
#     category
#     brand
#     IsStorno
#     gNumber


# order = {
#     "number": "", "date": "2021-05-27T06:19:47", "lastChangeDate": "2021-05-27T06:25:23",
#     "supplierArticle": "5240s2KolFianMal95p284", "techSize": "19", "barcode": "2000547259778",
#     "quantity": 1, "totalPrice": 1390, "discountPercent": 77, "isSupply": false,
#     "isRealization": true, "orderId": 23209536447, "promoCodeDiscount": 15,
#     "warehouseName": "Подольск", "countryName": "Россия",
#     "oblastOkrugName": "Сибирский федеральный округ", "regionName": "Кемеровская",
#     "incomeID": 1518243, "saleID": "S1465440585", "odid": 100462255958, "spp": 0, "forPay": 244.57,
#     "finishedPrice": 271, "priceWithDisc": 271.75, "nmId": 15456914, "subject": "Кольца",
#     "category": "Бижутерия", "brand": "Фабрика украшений", "IsStorno": 0,
#     "gNumber": "96535197125658677767"
# }
