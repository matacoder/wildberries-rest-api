import datetime
import logging
import os
from abc import abstractmethod
from email.utils import format_datetime

import requests


class RestClient:
    def __init__(self):
        self.token = os.getenv("WB_TOKEN")
        self.base_url = "https://suppliers-stats.wildberries.ru/api/v1/supplier/"

    @staticmethod
    def get_date():
        date = datetime.datetime.today()
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

    def get_ordered(self):
        params = {
            "dateFrom": self.get_date(),
            "key": self.token,
            "flag": 1,
        }
        return self.connect(params, self.base_url + "orders")


