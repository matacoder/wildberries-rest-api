import datetime
import logging
import time

import cachetools.func
import requests

from wb.models import ApiKey

RETRY_DELAY = 0.1


class RestClient:
    def __init__(self, user):
        self.token = ApiKey.objects.get(user=user.id).api
        self.base_url = "https://suppliers-stats.wildberries.ru/api/v1/supplier/"

    @staticmethod
    def get_date(week=None):
        date = datetime.datetime.today()
        if week:
            date = date - datetime.timedelta(days=(date.weekday()))
        return date.strftime("%Y-%m-%dT00:00:00.000Z")

    @staticmethod
    def connect(params, server):
        response = requests.get(url=server, params=params)
        logging.warning(f"{response.url}")
        return response

    def get_stock(self):
        params = {
            "dateFrom": self.get_date(),
            "key": self.token,
        }
        return self.connect(params, self.base_url + "stocks")

    def get_ordered(self, url, week=False, flag=1):
        params = {
            "dateFrom": self.get_date(week),
            "key": self.token,
            "flag": flag,
        }
        return self.connect(params, self.base_url + url)

    def get_report(self, url, week=False):
        params = {
            "dateFrom": self.get_date(week),
            "dateto": self.get_date(),
            "key": self.token,
        }
        return self.connect(params, self.base_url + url)


@cachetools.func.ttl_cache(maxsize=128, ttl=60 * 8)
def get_last_week(user):
    client = RestClient(user)
    data = client.get_report("reportDetailByPeriod", week=True).json()
    payment = sum((x["supplier_reward"]) for x in data)
    return int(payment)


@cachetools.func.ttl_cache(maxsize=128, ttl=60 * 9)
def get_weekly_payment(user):
    data = get_bought_products(user, week=True, flag=0)
    payment = sum((x["forPay"]) for x in data)
    return int(payment)


@cachetools.func.ttl_cache(maxsize=128, ttl=60 * 10)
def get_ordered_sum(user):
    data = get_ordered_products(user)
    return int(sum((x["totalPrice"] * (1 - x["discountPercent"] / 100)) for x in data))


@cachetools.func.ttl_cache(maxsize=128, ttl=60 * 11)
def get_bought_sum(user):
    data = get_bought_products(user, week=False)
    return int(sum((x["forPay"]) for x in data))


@cachetools.func.ttl_cache(maxsize=128, ttl=60 * 12)
def get_ordered_products(user):
    client = RestClient(user)
    data = client.get_ordered(url="orders")
    while data.status_code != 200:
        logging.warning("WB endpoint is faulty. Retrying...")
        time.sleep(RETRY_DELAY)
        data = client.get_ordered(url="orders")
    return data.json()


@cachetools.func.ttl_cache(maxsize=128, ttl=60 * 13)
def get_bought_products(user, week=False, flag=1):
    client = RestClient(user)
    data = client.get_ordered(url="sales", week=week, flag=flag)
    while data.status_code != 200:
        logging.warning("WB endpoint is faulty. Retrying...")
        time.sleep(RETRY_DELAY)
        data = client.get_ordered(url="sales", week=week, flag=flag)
    return data.json()


@cachetools.func.ttl_cache(maxsize=128, ttl=60 * 14)
def get_stock_products(user):
    client = RestClient(user)
    data = client.get_stock()
    while data.status_code != 200:
        logging.warning("WB endpoint is faulty. Retrying...")
        time.sleep(RETRY_DELAY)
        data = client.get_stock()
    return data.json()
