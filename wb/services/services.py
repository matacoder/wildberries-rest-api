import datetime
import functools
import time

import requests
from django.shortcuts import redirect
from loguru import logger

from wb.models import ApiKey
from wb.services.redis import redis_cache_decorator

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
    def __init__(self, token):
        self.token = token
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
        # redis_client.get_date
        response = requests.get(url=server, params=params)
        logger.info(f"URL WAS: {response.url}")
        return response

    def get_stock(self):
        logger.info("Preparing url params for stocks...")
        params = {
            "dateFrom": self.get_date(days=15),
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


@redis_cache_decorator()
def get_weekly_payment(token):
    logger.info("Getting weekly payment...")
    data = get_bought_products(token, week=True, flag=0)
    if data:
        payment = sum((x["forPay"]) for x in data)
        return int(payment)
    return 0


@redis_cache_decorator()
def get_ordered_sum(token):
    logger.info("Getting ordered payment...")
    data = get_ordered_products(token)
    if data:
        return int(
            sum((x["totalPrice"] * (1 - x["discountPercent"] / 100)) for x in data)
        )
    return 0


@redis_cache_decorator()
def get_bought_sum(token):
    logger.info("Getting bought payment...")
    data = get_bought_products(token)
    if data:
        return int(sum((x["forPay"]) for x in data))
    return 0


@redis_cache_decorator()
def get_ordered_products(token, week=False, flag=1, days=None):
    client = RestClient(token)
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


@redis_cache_decorator()
def get_bought_products(token, week=False, flag=1):
    client = RestClient(token)
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


@redis_cache_decorator()
def get_stock_products(token):
    """Getting products in stock."""
    logger.info("Getting products in stock.")
    client = RestClient(token)
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
