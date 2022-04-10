import datetime
import functools
import time

import cachetools.func
import requests
from django.shortcuts import redirect
from loguru import logger

from wb.models import ApiKey

RETRY_DELAY = 0.1


def api_key_required(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if ApiKey.objects.filter(user=args[0].user.id).exists():
            return func(*args, **kwargs)
        else:
            return redirect("api")

    return wrapper


class RestClient:
    def __init__(self, user):
        self.token = ApiKey.objects.get(user=user.id).api
        self.base_url = "https://suppliers-stats.wildberries.ru/api/v1/supplier/"

    @staticmethod
    def get_date(week=None, days=None):
        date = datetime.datetime.today()
        if days:
            date = date - datetime.timedelta(days=days)
        elif week:
            date = date - datetime.timedelta(days=(date.weekday()))
        return date.strftime("%Y-%m-%dT00:00:00.000Z")

    @staticmethod
    def connect(params, server):
        response = requests.get(url=server, params=params)
        logger.info(f"URL WAS: {response.url}")
        return response

    def get_stock(self):
        logger.info("Preparing url params for stocks...")
        params = {
            "dateFrom": self.get_date(),
            "key": self.token,
        }
        return self.connect(params, self.base_url + "stocks")

    def get_ordered(self, url, week=False, flag=1, days=None):
        params = {
            "dateFrom": self.get_date(week, days),
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
    logger.info("Getting weekly payment...")
    data = get_bought_products(user, week=True, flag=0)
    if data:
        payment = sum((x["forPay"]) for x in data)
        return int(payment)
    else:
        return "WB error"


@cachetools.func.ttl_cache(maxsize=128, ttl=60 * 10)
def get_ordered_sum(user):
    logger.info("Getting ordered payment...")
    data = get_ordered_products(user)
    if data:
        return int(
            sum((x["totalPrice"] * (1 - x["discountPercent"] / 100)) for x in data)
        )
    else:
        return "WB error"


@cachetools.func.ttl_cache(maxsize=128, ttl=60 * 11)
def get_bought_sum(user):
    logger.info("Getting bought payment...")
    data = get_bought_products(user, week=False)
    if data:
        return int(sum((x["forPay"]) for x in data))
    else:
        return "WB error"


@cachetools.func.ttl_cache(maxsize=128, ttl=60 * 12)
def get_ordered_products(user, week=False, flag=1, days=None):

    client = RestClient(user)
    data = client.get_ordered(url="orders", week=week, flag=flag, days=days)
    attempt = 0
    while data.status_code != 200:
        attempt += 1
        if attempt > 10:
            return {}
        logger.info("WB endpoint is faulty. Retrying...")
        time.sleep(RETRY_DELAY)
        data = client.get_ordered(url="orders", week=week, flag=flag, days=days)
    return data.json()


@cachetools.func.ttl_cache(maxsize=128, ttl=60 * 13)
def get_bought_products(user, week=False, flag=1):
    client = RestClient(user)
    data = client.get_ordered(url="sales", week=week, flag=flag)
    attempt = 0
    while data.status_code != 200:
        attempt += 1
        if attempt > 10:
            return {}
        logger.info("WB endpoint is faulty. Retrying...")
        time.sleep(RETRY_DELAY)
        data = client.get_ordered(url="sales", week=week, flag=flag)
    return data.json()


@cachetools.func.ttl_cache(maxsize=128, ttl=60 * 14)
def get_stock_products(user):
    """Getting products in stock."""
    logger.info("Getting products in stock.")
    client = RestClient(user)
    data = client.get_stock()
    logger.info(data)
    attempt = 0
    while data.status_code != 200:
        attempt += 1
        if attempt > 10:
            return {}
        logger.info("WB endpoint is faulty. Retrying...")
        time.sleep(RETRY_DELAY)
        data = client.get_stock()
    logger.info(data.text[:100])
    return data.json()
