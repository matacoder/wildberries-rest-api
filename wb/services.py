import datetime
import functools
import json
import pickle
import time
from threading import Thread
from typing import Callable


import requests

from django.shortcuts import redirect
from loguru import logger

from _settings.settings import redis_client
from wb.models import ApiKey

RETRY_DELAY = 0.1

running_threads = set()


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
        # redis_client.get_date
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


def redis_cache_decorator(func: Callable):
    @functools.wraps(func)
    def wrapper(user, *args, **kwargs):
        logger.info(f"Redis decorator for {func.__name__}")
        api_key = ApiKey.objects.get(user=user).api
        args_key = "args" + json.dumps(args) + json.dumps(kwargs)
        redis_full_key = f"{api_key}:{func.__name__}:{args_key}"
        redis_timestamp_key = f"{redis_full_key}:updated_at"

        cached_result = redis_client.get(redis_full_key)
        timestamp = redis_client.get(redis_timestamp_key)
        current_time = datetime.datetime.now()

        threshold = datetime.timedelta(minutes=10)

        def run_and_cache():
            global running_threads
            running_threads.add(redis_full_key)
            result = func(user, *args, **kwargs)
            redis_client.set(redis_full_key, json.dumps(result))
            redis_client.set(redis_timestamp_key, pickle.dumps(current_time))
            logger.info(f"Redis decorator for {func.__name__}: finished calc in thread!")
            running_threads.remove(redis_full_key)
            return result

        if not cached_result:
            logger.info(f"Redis decorator for {func.__name__}: not found, calculating")
            cached_result = run_and_cache()
        else:
            cached_result = json.loads(cached_result)
            if redis_full_key not in running_threads:
                if not timestamp:
                    timestamp = current_time - datetime.timedelta(minutes=11)
                    redis_client.set(redis_timestamp_key, pickle.dumps(current_time))
                else:
                    timestamp = pickle.loads(timestamp)
                if current_time - timestamp > threshold:
                    logger.info(f"Redis decorator for {func.__name__}: found! Running update in thread...")
                    thread = Thread(target=run_and_cache)
                    thread.start()
                else:
                    logger.info(f"Less than 10 minutes passed since previous check for {func.__name__}")
            else:
                logger.info(f"Redis decorator for {func.__name__}: is already running")
        return cached_result

    return wrapper


@redis_cache_decorator
def get_weekly_payment(user):
    logger.info("Getting weekly payment...")
    data = get_bought_products(user, week=True, flag=0)
    if data:
        payment = sum((x["forPay"]) for x in data)
        return int(payment)
    else:
        return "WB error"


@redis_cache_decorator
def get_ordered_sum(user):
    logger.info("Getting ordered payment...")
    data = get_ordered_products(user)
    if data:
        return int(
            sum((x["totalPrice"] * (1 - x["discountPercent"] / 100)) for x in data)
        )
    else:
        return "WB error"


@redis_cache_decorator
def get_bought_sum(user):
    logger.info("Getting bought payment...")
    data = get_bought_products(user, week=False)
    if data:
        return int(sum((x["forPay"]) for x in data))
    else:
        return "WB error"


@redis_cache_decorator
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


@redis_cache_decorator
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


@redis_cache_decorator
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
